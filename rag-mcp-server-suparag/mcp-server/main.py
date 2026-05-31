#!/usr/bin/env python3
"""
Contextual RAG MCP Server with Streamable HTTP Transport (MCP 2025-11-25)
Thin wrapper around existing authenticRAG.py
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Optional
import uuid

from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import asyncio
import json

# Add authenticRAG.py to path (mounted as volume)
sys.path.insert(0, '/app/rag')

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

# Global RAG client
rag_client = None


# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Contextual RAG MCP Server (Streamable HTTP)...")
    await initialize_rag_client()
    yield
    logger.info("Shutting down Contextual RAG MCP Server...")


# Create FastAPI application
app = FastAPI(
    title="Contextual RAG MCP Server",
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


async def initialize_rag_client():
    """Initialize RAG client (wrapper around authenticRAG.py)"""
    global rag_client
    
    try:
        logger.info("Initializing Contextual RAG client...")
        
        # Import existing authenticRAG module
        from authenticRAG import AnthropicStyleContextualRAG
        
        # Get configuration from environment
        opensearch_host = os.getenv("OPENSEARCH_HOST", "opensearch")
        opensearch_port = int(os.getenv("OPENSEARCH_PORT", "9200"))
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
        # Initialize RAG client with Ollama
        rag_client = AnthropicStyleContextualRAG(
            opensearch_host=opensearch_host,
            opensearch_port=opensearch_port,
            ollama_url=ollama_url
        )
        
        logger.info(f"✅ Contextual RAG client initialized (OpenSearch: {opensearch_host}:{opensearch_port}, Ollama: {ollama_url})")
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG client: {e}", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "contextual-rag-mcp-server",
        "rag_client": "initialized" if rag_client else "not_initialized"
    }


@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "Contextual RAG MCP Server",
        "version": "1.0.0",
        "transport": "Streamable HTTP",
        "protocol_version": "2025-11-25",
        "endpoint": "/mcp",
        "features": [
            "Contextual Retrieval",
            "Hybrid Search (BM25 + Vector + RRF)",
            "Dual Indexing (OpenSearch)",
            "Qwen API Context Generation",
            "Ollama BGE-M3 Embeddings"
        ]
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
                        "name": "contextual-rag-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            tools = [
                {
                    "name": "search_documentation",
                    "description": "Search with Contextual Retrieval (Hybrid: BM25 + Vector + RRF)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "number", "default": 5, "description": "Number of results"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "add_documents",
                    "description": "Index documents with context generation (Qwen API)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to document or directory"}
                        },
                        "required": ["path"]
                    }
                }
                # {
                #     "name": "generate_answer",
                #     "description": "Generate answer using RAG pipeline",
                #     "inputSchema": {
                #         "type": "object",
                #         "properties": {
                #             "query": {"type": "string", "description": "Question to answer"},
                #             "use_context": {"type": "boolean", "default": True, "description": "Use search context"}
                #         },
                #         "required": ["query"]
                #     }
                # }
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
            
            # Execute tool
            if name == "search_documentation":
                result = await search_documentation(**arguments)
            elif name == "add_documents":
                result = await add_documents(**arguments)
            # elif name == "generate_answer":
            #     result = await generate_answer(**arguments)
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


# Tool implementations
async def search_documentation(query: str, limit: int = 5) -> str:
    """Search with Contextual Retrieval"""
    try:
        if not rag_client:
            return "Error: RAG client not initialized"
        
        logger.info(f"Searching: '{query}' (limit={limit})")
        
        # Use hybrid_search method
        results = rag_client.hybrid_search(query, k=limit)
        
        if not results or len(results) == 0:
            return "No results found for your query."
        
        formatted = []
        for i, (doc_id, score, source) in enumerate(results, 1):
            content = source.get('content', '')
            context = source.get('contextualized_content', '')
            
            formatted.append(
                f"[{i}] Document {doc_id} (RRF Score: {score:.4f})\n"
                f"Context: {context}\n\n"
                f"Content: {content[:300]}{'...' if len(content) > 300 else ''}\n"
            )
        
        return "\n---\n".join(formatted)
    
    except Exception as e:
        logger.error(f"Error searching: {e}", exc_info=True)
        return f"Error searching: {str(e)}"


async def add_documents(path: str) -> str:
    """Index documents with context generation"""
    try:
        import os
        from pathlib import Path
        
        if not rag_client:
            return "Error: RAG client not initialized"
        
        logger.info(f"Indexing documents from: {path}")
        
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        # Get all markdown files
        md_files = []
        if os.path.isfile(path):
            if path.endswith('.md'):
                md_files = [path]
        elif os.path.isdir(path):
            md_files = list(Path(path).glob('*.md'))
            md_files = [str(f) for f in md_files]
        
        if not md_files:
            return f"No markdown files found in: {path}"
        
        logger.info(f"Found {len(md_files)} markdown files")
        
        # Load and chunk documents
        docs = rag_client.load_documents(md_files)
        
        if not docs:
            return "No documents could be loaded"
        
        logger.info(f"Loaded {len(docs)} chunks")
        
        # Index with context generation
        indexed_count = rag_client.add_documents_with_context(docs)
        
        return f"""✅ Successfully indexed documents with Contextual Retrieval:
- Files processed: {len(md_files)}
- Chunks created: {len(docs)}
- Contexts generated: {indexed_count}
- Indexed to OpenSearch: {indexed_count}
- Vector index: anthropic-vector-index
- BM25 index: anthropic-bm25-index

Files: {', '.join([os.path.basename(f) for f in md_files])}"""
    
    except Exception as e:
        return f"Error indexing documents: {str(e)}"


# async def generate_answer(query: str, use_context: bool = True) -> str:
#     """Generate answer using RAG pipeline"""
#     try:
#         if not rag_client:
#             return "Error: RAG client not initialized"
#         
#         logger.info(f"Generating answer for: '{query}' (use_context={use_context})")
#         
#         if use_context:
#             # Use search_for_question which does hybrid search + answer generation
#             answer = rag_client.search_for_question(query, k=5)
#         else:
#             # Direct answer without context using call_qwen_api
#             answer = rag_client.call_qwen_api(query)
#         
#         return answer
#     
#     except Exception as e:
#         logger.error(f"Error generating answer: {e}", exc_info=True)
#         return f"Error generating answer: {str(e)}"


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8001"))
    
    logger.info(f"Starting MCP server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
