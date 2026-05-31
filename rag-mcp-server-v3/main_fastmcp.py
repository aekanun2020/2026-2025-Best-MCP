#!/usr/bin/env python3
"""
PyRAGDoc MCP Server with SSE Transport using FastMCP
Main application entry point
"""
import os
import sys
import logging
import asyncio

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

from pyragdoc.config import load_config
from pyragdoc.core.embedding import create_embedding_service
from pyragdoc.core.storage import create_storage_service
from app.rag_services import initialize_services
from app import mcp_server

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_rag_services():
    """Initialize RAG services"""
    try:
        config = load_config()
        logger.info("Initializing RAG services...")
        
        # Create services
        embedding_service = create_embedding_service(config["embedding"])
        storage_service = create_storage_service(config["database"])
        
        # Set vector size in storage service
        vector_size = embedding_service.get_vector_size()
        storage_service.vector_size = vector_size
        
        # Initialize storage
        await storage_service.initialize()
        
        # Initialize services in app modules
        initialize_services(embedding_service, storage_service)
        
        logger.info("RAG services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

async def main():
    """Main entry point"""
    # Initialize RAG services
    await initialize_rag_services()
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Create SSE transport
    transport = SseServerTransport("/messages")
    
    logger.info(f"Starting PyRAGDoc MCP Server on {host}:{port}")
    logger.info(f"SSE endpoint: http://{host}:{port}/sse")
    logger.info(f"Messages endpoint: http://{host}:{port}/messages")
    
    # Run the server using FastMCP's built-in SSE server
    async with mcp_server.mcp_server.run_sse_server(
        host=host,
        port=port,
        transport=transport
    ) as server:
        logger.info("Server is running...")
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
