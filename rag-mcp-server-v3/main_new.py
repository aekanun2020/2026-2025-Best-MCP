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

from pyragdoc.config import load_config
from pyragdoc.core.embedding import create_embedding_service
from pyragdoc.core.storage import create_storage_service
from app.rag_services import initialize_services

# Import the FastMCP server instance
from app.mcp_server import mcp_server

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
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Initialize services first
    asyncio.run(initialize_rag_services())
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting PyRAGDoc MCP Server on {host}:{port}")
    
    # Run the FastMCP server with SSE transport
    mcp_server.run(transport="sse", host=host, port=port)
