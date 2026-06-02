#!/usr/bin/env python3
"""
MSSQL MCP Server with Streamable HTTP Transport
Main application entry point
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import asyncio
import json
import uuid

from app.mcp_server import mcp_server, streamable_http_transport
from app.database import db_cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Streamable HTTP sessions storage
mcp_sessions = {}

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting MCP Streamable HTTP Server...")
    # Initialize database cache
    db_cache.refresh()
    yield
    # Cleanup resources here
    logger.info("Shutting down MCP Streamable HTTP Server...")

# Create FastAPI application
app = FastAPI(
    title="MSSQL MCP Server",
    description="Model Context Protocol server for MSSQL with Streamable HTTP transport",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)


def validate_origin(request: Request) -> Optional[JSONResponse]:
    """Validate the Origin header to prevent DNS rebinding attacks.

    Per the Streamable HTTP spec, if an Origin header is present and invalid,
    the server MUST respond with HTTP 403 Forbidden. Allowed origins can be
    configured via the ALLOWED_ORIGINS environment variable (comma separated);
    when unset, all origins are accepted (development default).
    """
    origin = request.headers.get("origin")
    if not origin:
        return None

    allowed = os.getenv("ALLOWED_ORIGINS", "*")
    if allowed.strip() == "*":
        return None

    allowed_origins = [o.strip() for o in allowed.split(",") if o.strip()]
    if origin not in allowed_origins:
        logger.warning(f"Rejected request with invalid Origin: {origin}")
        return JSONResponse(
            status_code=403,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Origin"
                }
            }
        )
    return None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "service": "mssql-mcp-server",
        "transport": "streamable-http"
    }

# Root endpoint
@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "MSSQL MCP Server",
        "version": "1.0.0",
        "transport": "Streamable HTTP",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health"
        }
    }

# MCP endpoint - single endpoint supporting POST, GET, and DELETE
@app.api_route("/mcp", methods=["POST", "GET", "DELETE"])
async def mcp_endpoint(request: Request):
    """Streamable HTTP endpoint for MCP communication.

    A single MCP endpoint that supports:
      - POST   : client sends a JSON-RPC request/notification/response
      - GET     : open an SSE stream for server-initiated messages
      - DELETE : explicitly terminate a session
    """
    # Validate Origin header (DNS rebinding protection)
    origin_error = validate_origin(request)
    if origin_error is not None:
        return origin_error

    if request.method == "DELETE":
        return await handle_delete(request)
    elif request.method == "GET":
        return await handle_get(request)
    else:
        return await handle_post(request)


async def handle_post(request: Request):
    """Handle POST requests carrying JSON-RPC messages."""
    try:
        # Parse JSON-RPC message
        message = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON in POST body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    method = message.get("method")

    # Stateless session handling (matches FastMCP's stateless_http=True).
    # The server does NOT require clients to track or echo an Mcp-Session-Id:
    # every request is processed independently. On initialize we still mint a
    # session id and return it in the response header, so spec-compliant
    # stateful clients can use it if they wish -- but clients that omit it
    # (e.g. simple Streamable HTTP clients) are accepted, not rejected. This
    # avoids the 400 "Missing Mcp-Session-Id header" that stateful mode raised.
    session_id = request.headers.get("mcp-session-id")

    if method == "initialize":
        # Mint a session id for clients that want to track one (optional).
        session_id = str(uuid.uuid4())
        mcp_sessions[session_id] = {"queue": asyncio.Queue()}
        logger.info(f"New MCP session (stateless mode): {session_id}")
    # Non-initialize requests are accepted with or without a session id.
    # (No 400/404 enforcement -- stateless.)

    # If the input is a notification or response (no id), accept with 202.
    if "id" not in message or message.get("id") is None:
        if method is not None and method.startswith("notifications/"):
            return Response(status_code=202)

    # Process MCP message and get response
    response = await process_mcp_message(message)

    if response is None:
        # Nothing to return (e.g. a notification) -> 202 Accepted, no body
        return Response(status_code=202)

    # Return a single JSON object (application/json), as permitted by the spec.
    headers = {}
    if method == "initialize" and session_id:
        headers["Mcp-Session-Id"] = session_id

    return JSONResponse(response, headers=headers)


async def handle_get(request: Request):
    """Handle GET requests for opening a server-to-client SSE stream.

    This server does not initiate server-to-client requests on a standalone
    stream, so per the spec it returns HTTP 405 Method Not Allowed.
    """
    return Response(status_code=405)


async def handle_delete(request: Request):
    """Handle DELETE requests to explicitly terminate a session.

    Stateless mode: there is no mandatory session, so termination is a no-op
    that always succeeds. If the client did track a minted session id we clean
    it up; either way we return 200.
    """
    session_id = request.headers.get("mcp-session-id")
    if session_id and session_id in mcp_sessions:
        del mcp_sessions[session_id]
        logger.info(f"Terminated MCP session: {session_id}")
    return Response(status_code=200)


async def process_mcp_message(message: dict) -> Optional[dict]:
    """Process an MCP message and return response."""
    try:
        method = message.get("method")
        params = message.get("params", {})
        message_id = message.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "mssql-streamable-http-server",
                        "version": "1.0.0"
                    }
                }
            }
        elif method == "tools/list":
            # Get tools from MCP server
            tools = [
                {
                    "name": "get_database_context",
                    "description": """Get complete database context including schema, relationships, and T-SQL syntax guide.

⚠️ IMPORTANT: Call this tool FIRST before executing any queries.

Returns comprehensive information:
• Database metadata (name, tables, size)
• Complete table schemas (all columns, types)
• Relationship graph (foreign keys, standalone tables)
• T-SQL syntax guide (TOP, GETDATE, etc.)
• Common query examples

No parameters required.""",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "execute_query_tool",
                    "description": "Execute a T-SQL query on the database. Use get_database_context first to understand the schema and syntax.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "T-SQL query to execute"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "preview_table",
                    "description": "Get a preview of the data in a table",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "table_name": {"type": "string", "description": "Name of the table to preview"},
                            "limit": {"type": "number", "description": "Maximum number of rows to return", "default": 10}
                        },
                        "required": ["table_name"]
                    }
                },
                {
                    "name": "get_database_info_tool",
                    "description": "Get general information about the database (name, table count, size, version). No parameters required.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "refresh_db_cache",
                    "description": "Refresh the database schema cache",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                }
            ]
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "tools": tools
                }
            }
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Import tool functions
            from app.mcp_server import (
                execute_query_tool, preview_table, get_database_info_tool, 
                refresh_db_cache, get_database_context
            )
            
            # Call the appropriate tool
            if name == "get_database_context":
                result = await get_database_context()
            elif name == "execute_query_tool":
                result = await execute_query_tool(**arguments)
            elif name == "preview_table":
                result = await preview_table(**arguments)
            elif name == "get_database_info_tool":
                result = await get_database_info_tool()
            elif name == "refresh_db_cache":
                result = await refresh_db_cache()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": f"Unknown tool: {name}"
                    }
                }
            
            # Parse result and format response
            try:
                result_data = json.loads(result)
                content = result_data.get("result", result_data.get("error", result))
            except:
                content = result
            
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(content)
                        }
                    ]
                }
            }
        elif method == "resources/list":
            resources = [
                {
                    "uri": "mssql://tables",
                    "name": "Database Tables",
                    "description": "List all tables in the database"
                },
                {
                    "uri": "mssql://schema/{table_name}",
                    "name": "Table Schema",
                    "description": "Get the schema for a specific table"
                }
            ]
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "resources": resources
                }
            }
        elif method == "resources/read":
            uri = params.get("uri")
            
            # Import resource functions
            from app.mcp_server import list_tables, get_schema
            
            if uri == "mssql://tables":
                result = await list_tables()
            elif uri and uri.startswith("mssql://schema/"):
                table_name = uri.replace("mssql://schema/", "")
                result = await get_schema(table_name)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid params",
                        "data": f"Unknown resource URI: {uri}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": result
                        }
                    ]
                }
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error processing MCP message: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True if os.getenv("ENVIRONMENT", "development") == "development" else False,
        log_level="info"
    )
