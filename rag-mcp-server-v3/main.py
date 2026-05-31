#!/usr/bin/env python3
"""
PyRAGDoc MCP Server with SSE Transport (MCP 2024-11-05)
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
search_orchestrator = None  # NEW: Search orchestrator for hybrid search

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting PyRAGDoc MCP Server (SSE Transport)...")
    await initialize_rag_services()
    yield
    logger.info("Shutting down PyRAGDoc MCP Server...")

# Create FastAPI application
app = FastAPI(
    title="PyRAGDoc MCP Server",
    description="Model Context Protocol server with SSE transport",
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
        global embedding_service, storage_service, search_orchestrator
        
        config = load_config()
        logger.info("Initializing RAG services...")
        
        # Initialize embedding and storage services
        embedding_service = create_embedding_service(config["embedding"])
        storage_service = create_storage_service(config["database"])
        
        vector_size = embedding_service.get_vector_size()
        storage_service.vector_size = vector_size
        
        await storage_service.initialize()
        
        # NEW: Initialize hybrid search components
        logger.info("Initializing hybrid search components...")
        from pyragdoc.utils.thai_tokenizer import ThaiTokenizer
        from pyragdoc.core.bm25 import BM25Retriever
        from pyragdoc.core.rrf import RRFCombiner
        from pyragdoc.core.search import SearchOrchestrator
        
        # Create Thai tokenizer
        thai_tokenizer = ThaiTokenizer()
        
        # Create BM25 retriever
        bm25_retriever = BM25Retriever(thai_tokenizer)
        
        # Create RRF combiner
        rrf_combiner = RRFCombiner(k=60)
        
        # Create search orchestrator
        search_orchestrator = SearchOrchestrator(
            bm25_retriever=bm25_retriever,
            storage_service=storage_service,
            embedding_service=embedding_service,
            rrf_combiner=rrf_combiner,
            default_mode="hybrid"
        )
        
        # Build BM25 index from existing Qdrant documents
        await build_bm25_index(bm25_retriever, storage_service)
        
        # Initialize app services
        initialize_services(embedding_service, storage_service, search_orchestrator)
        
        logger.info("RAG services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def build_bm25_index(bm25_retriever, storage_service):
    """Build BM25 index from existing Qdrant documents with pagination"""
    try:
        logger.info("Building BM25 index from existing documents...")
        
        from pyragdoc.models.documents import DocumentChunk, DocumentMetadata
        import datetime
        
        all_chunks = []
        offset = None
        batch_size = 1000
        total_processed = 0
        
        # Paginate through all documents
        while True:
            # Scroll with offset for pagination
            scroll_result = await asyncio.to_thread(
                storage_service.client.scroll,
                collection_name=storage_service.collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_offset = scroll_result
            
            if not points:
                break
            
            # Convert points to DocumentChunk objects
            for point in points:
                payload = point.payload
                
                # Extract metadata
                metadata_dict = payload.get("metadata", {})
                metadata = DocumentMetadata(**metadata_dict)
                
                # Extract text and timestamp
                text = payload.get("text", "")
                timestamp_str = payload.get("timestamp")
                timestamp = datetime.datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.datetime.now()
                
                # Create DocumentChunk
                chunk = DocumentChunk(
                    text=text,
                    metadata=metadata,
                    id=str(point.id),
                    timestamp=timestamp
                )
                all_chunks.append(chunk)
            
            total_processed += len(points)
            logger.info(f"Loaded {total_processed} documents from Qdrant...")
            
            # Check if there are more documents
            if next_offset is None:
                break
            
            offset = next_offset
        
        # Index all documents in BM25
        if all_chunks:
            logger.info(f"Building BM25 index for {len(all_chunks)} documents...")
            await bm25_retriever.index_documents(all_chunks)
            logger.info(f"✅ BM25 index built successfully with {len(all_chunks)} documents")
        else:
            logger.info("No documents to index in BM25")
            
    except Exception as e:
        logger.error(f"Failed to build BM25 index: {e}", exc_info=True)
        logger.warning("⚠️  Continuing without BM25 index - hybrid search will fall back to semantic only")

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
        "transport": "SSE",
        "protocol_version": "2024-11-05",
        "endpoint": "/sse"
    }

# Main MCP endpoint - supports both GET and POST
# Also support /sse for backward compatibility
@app.get("/mcp")
@app.get("/sse")
async def mcp_get(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="MCP-Session-Id"),
    session_id: Optional[str] = None  # Query parameter for backward compatibility
):
    """GET endpoint for opening SSE stream (optional feature)"""
    # Support both header and query parameter
    sid = mcp_session_id or session_id
    
    # Create or reuse session
    if not sid or sid not in sessions:
        session_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        sessions[session_id] = queue
        logger.info(f"New SSE session created: {session_id}")
    else:
        session_id = sid
        logger.info(f"Reusing SSE session: {session_id}")
    
    async def event_stream():
        try:
            queue = sessions.get(session_id)
            if not queue:
                return
            
            # Send endpoint event for old spec compatibility
            endpoint_url = f"/messages?session_id={session_id}"
            yield f"event: endpoint\ndata: {endpoint_url}\n\n"
            
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    # Send as SSE message event
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keep-alive every 15 seconds to prevent client timeout
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
@app.post("/messages")  # Backward compatibility with old spec
async def mcp_post(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="MCP-Session-Id"),
    mcp_protocol_version: Optional[str] = Header(None, alias="MCP-Protocol-Version"),
    session_id: Optional[str] = None  # Query parameter for backward compatibility
):
    """POST endpoint for sending JSON-RPC messages"""
    try:
        # Support both header and query parameter
        sid = mcp_session_id or session_id
        
        # Parse JSON-RPC message
        message = await request.json()
        method = message.get("method")
        
        logger.info(f"Received {method} request, session={sid}")
        
        # Process message
        response = await process_mcp_message(message)
        
        if not response:
            return JSONResponse({"status": "received"})
        
        # For initialize, create session and return with header
        if method == "initialize":
            new_session_id = str(uuid.uuid4())
            sessions[new_session_id] = asyncio.Queue()
            logger.info(f"Created session for initialize: {new_session_id}")
            
            # Send response via existing SSE stream if available
            if sid and sid in sessions:
                try:
                    await sessions[sid].put(response)
                    logger.info(f"Initialize response queued to SSE for session {sid}")
                except Exception as e:
                    logger.error(f"Failed to queue initialize response to SSE: {e}")
            
            # Also return in HTTP body with new session header
            return JSONResponse(response, headers={"MCP-Session-Id": new_session_id})
        
        # Send via SSE if session exists (spec 2024-11-05 behavior)
        if sid and sid in sessions:
            try:
                # Try to queue with a short timeout to detect dead connections
                await asyncio.wait_for(sessions[sid].put(response), timeout=1.0)
                logger.info(f"Response queued to SSE for session {sid}")
                # Return 202 Accepted - response will come via SSE
                return Response(status_code=202)
            except asyncio.TimeoutError:
                logger.warning(f"SSE queue full or dead for session {sid}, falling back to HTTP body")
                # SSE connection might be dead - fallback to HTTP body
                return JSONResponse(response)
            except Exception as e:
                logger.error(f"Failed to queue to SSE: {e}")
                # Fallback to HTTP body if SSE fails
                return JSONResponse(response)
        
        # No session - return in HTTP body
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.delete("/mcp")
@app.delete("/messages")  # Backward compatibility
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
                    "protocolVersion": "2024-11-05",
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
                            "limit": {"type": "number", "default": 5},
                            "search_mode": {"type": "string", "default": "hybrid", "enum": ["hybrid", "bm25", "semantic"]}
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
                },
                {
                    "name": "add_context",
                    "description": "Add context content directly to the RAG database",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The text content to add"},
                            "title": {"type": "string", "description": "Optional title for the content"},
                            "source": {"type": "string", "default": "agent_context", "description": "Source identifier"},
                            "metadata": {"type": "object", "description": "Optional additional metadata"}
                        },
                        "required": ["content"]
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
            
            from app.mcp_server import search_documentation, list_sources, add_directory, add_context
            
            if name == "search_documentation":
                result = await search_documentation(**arguments)
            elif name == "list_sources":
                result = await list_sources()
            elif name == "add_directory":
                result = await add_directory(**arguments)
            elif name == "add_context":
                result = await add_context(**arguments)
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
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
