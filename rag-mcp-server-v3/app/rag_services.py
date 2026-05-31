"""
RAG Services initialization and management
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global service instances
embedding_service: Optional[object] = None
storage_service: Optional[object] = None
search_orchestrator: Optional[object] = None  # NEW: Search orchestrator

def initialize_services(embedding_svc, storage_svc, search_orch=None):
    """Initialize global service instances
    
    Args:
        embedding_svc: Embedding service instance
        storage_svc: Storage service instance
        search_orch: Search orchestrator instance (optional)
    """
    global embedding_service, storage_service, search_orchestrator
    embedding_service = embedding_svc
    storage_service = storage_svc
    search_orchestrator = search_orch
    
    # Also update mcp_server services
    import app.mcp_server as mcp
    mcp.embedding_service = embedding_svc
    mcp.storage_service = storage_svc
    mcp.search_orchestrator = search_orch  # NEW
    
    logger.info("RAG services initialized in app modules")

def get_embedding_service():
    """Get the embedding service instance"""
    return embedding_service

def get_storage_service():
    """Get the storage service instance"""
    return storage_service

def get_search_orchestrator():
    """Get the search orchestrator instance"""
    return search_orchestrator
