#!/usr/bin/env python3
"""
PyRAGDoc MCP Server with Streamable HTTP Transport (MCP 2025-11-25)
Main application entry point
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import uuid

from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import asyncio
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyragdoc.config import load_config
from pyragdoc.core.embedding import create_embedding_service
from pyragdoc.core.storage import create_storage_service
from app.rag_services import initialize_services

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Session storage: session_id -> queue
sessions = {}

# Global service instances
embedding_service = None
storage_service = None

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting PyRAGDoc MCP Server (Streamable HTTP)...")
    await initialize_rag_services()
    yield
    logger.info("Shutting down PyRAGDoc MCP Server...")

# Create FastAPI application
app = FastAPI(
    title="PyRAGDoc MCP Server",
    description="Model Context Protocol server with Streamable HTTP transport",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_rag_services():
    """Initialize RAG services"""
    try:
        global embedding_service, storage_service
        
        config = load_config()
        logger.info("Initializing RAG services...")
        
        embedding_service = create_embedding_service(config["embedding"])
        storage_service = create_storage_service(config["database"])
        
        vector_size = embedding_service.get_vector_size()
        storage_service.vector_size = vector_size
        
        await storage_service.initialize()
        initialize_services(embedding_service, storage_service)
        
        logger.info("RAG services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pyragdoc-mcp-server"}

@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "PyRAGDoc MCP Server",
        "version": "1.0.0",
        "transport": "Streamable HTTP",
        "protocol_version": "2025-11-25",
        "endpoint": "/mcp"
    }

# Main MCP endpoint - supports both GET and POST
@app.get("/mcp")
async def mcp_get(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="MCP-Session-Id")
):
    """GET endpoint for opening SSE stream (optional feature)"""
    accept = request.headers.get("accept", "")
    
    if "text/event-stream" not in accept:
        return Response(status_code=405, content="Method Not Allowed")
    
    # Create or reuse session
    if not mcp_session_id or mcp_session_id not in sessions:
        session_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        sessions[session_id] = queue
        logger.info(f"New SSE session created: {session_id}")
    else:
        session_id = mcp_session_id
        logger.info(f"Reusing SSE session: {session_id}")
    
    async def event_stream():
        try:
            queue = sessions.get(session_id)
            if not queue:
                return
            
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=300.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keep-alive\n\n"
                    continue
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled: {session_id}")
        finally:
            if session_id in sessions:
                del sessions[session_id]
                logger.info(f"Cleaned up session: {session_id}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.post("/mcp")
async def mcp_post(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="MCP-Session-Id"),
    mcp_protocol_version: Optional[str] = Header(None, alias="MCP-Protocol-Version")
):
    """POST endpoint for sending JSON-RPC messages"""
    try:
        # Parse JSON-RPC message
        message = await request.json()
        method = message.get("method")
        
        logger.info(f"Received {method} request, session={mcp_session_id}")
        
        # Process message
        response = await process_mcp_message(message)
        
        if not response:
            return JSONResponse({"status": "received"})
        
        # For initialize, create session and return with header
        if method == "initialize":
            session_id = str(uuid.uuid4())
            sessions[session_id] = asyncio.Queue()
            logger.info(f"Created session for initialize: {session_id}")
            
            return JSONResponse(
                response,
                headers={"MCP-Session-Id": session_id}
            )
        
        # For other requests, return JSON response directly
        # This is simpler and works for most clients
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.delete("/mcp")
async def mcp_delete(
    mcp_session_id: Optional[str] = Header(None, alias="MCP-Session-Id")
):
    """DELETE endpoint for terminating session"""
    if mcp_session_id and mcp_session_id in sessions:
        del sessions[mcp_session_id]
        logger.info(f"Session terminated: {mcp_session_id}")
        return Response(status_code=204)
    return Response(status_code=404)

async def process_mcp_message(message: dict) -> Optional[dict]:
    """Process an MCP message and return response"""
    try:
        method = message.get("method")
        params = message.get("params", {})
        message_id = message.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "pyragdoc-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            tools = [
                {
                    "name": "search_documentation",
                    "description": "Search through stored documentation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "number", "default": 5}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "list_sources",
                    "description": "List all documentation sources",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "add_directory",
                    "description": "Add files from a directory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            ]
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"Executing tool: {name}")
            
            from app.mcp_server import search_documentation, list_sources, add_directory
            
            if name == "search_documentation":
                result = await search_documentation(**arguments)
            elif name == "list_sources":
                result = await list_sources()
            elif name == "add_directory":
                result = await add_directory(**arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "content": [{"type": "text", "text": str(result)}]
                }
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
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
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "main_streamable:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
