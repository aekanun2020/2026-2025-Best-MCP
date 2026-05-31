"""
Unit tests for MCP server integration with hybrid search.

These tests verify that the search_documentation tool correctly handles
different search modes and integrates with the SearchOrchestrator.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pyragdoc.models.documents import DocumentChunk, DocumentMetadata, SearchResult


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    # Mock embedding service
    mock_embedding = AsyncMock()
    mock_embedding.generate_embedding = AsyncMock(return_value=[0.1] * 384)
    
    # Mock storage service
    mock_storage = AsyncMock()
    
    # Mock search orchestrator
    mock_orchestrator = AsyncMock()
    
    return {
        'embedding': mock_embedding,
        'storage': mock_storage,
        'orchestrator': mock_orchestrator
    }


@pytest.fixture
def sample_results():
    """Create sample search results."""
    chunks = [
        DocumentChunk(
            text="This is a test document about Thai regulations.",
            metadata=DocumentMetadata(
                source="test.pdf",
                title="Test Document",
                url="http://example.com/test.pdf"
            ),
            id="doc_1",
            timestamp=datetime.now()
        ),
        DocumentChunk(
            text="Another document with relevant information.",
            metadata=DocumentMetadata(
                source="test2.pdf",
                title="Test Document 2"
            ),
            id="doc_2",
            timestamp=datetime.now()
        )
    ]
    
    return [
        SearchResult(chunk=chunks[0], score=0.95),
        SearchResult(chunk=chunks[1], score=0.82)
    ]


class TestSearchDocumentationTool:
    """Test the search_documentation MCP tool."""
    
    @pytest.mark.asyncio
    async def test_search_with_no_search_mode_defaults_to_hybrid(self, mock_services, sample_results):
        """
        Test that search_documentation defaults to hybrid mode when no mode specified.
        
        Validates: Requirements 5.1, 5.2
        """
        # Setup
        mock_services['orchestrator'].search = AsyncMock(return_value=sample_results)
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(query="test query", limit=5)
            
            # Verify: orchestrator.search called with default mode
            mock_services['orchestrator'].search.assert_called_once()
            call_args = mock_services['orchestrator'].search.call_args
            assert call_args[0][0] == "test query"
            assert call_args[0][1] == 5
            assert call_args[0][2] == "hybrid"  # Default mode
            
            # Verify: result is formatted string
            assert isinstance(result, str)
            assert "Test Document" in result
            assert "0.95" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_with_semantic_mode(self, mock_services, sample_results):
        """
        Test that search_documentation uses semantic mode when specified.
        
        Validates: Requirements 5.1, 5.3
        """
        # Setup
        mock_services['orchestrator'].search = AsyncMock(return_value=sample_results)
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(
                query="test query",
                limit=5,
                search_mode="semantic"
            )
            
            # Verify: orchestrator.search called with semantic mode
            mock_services['orchestrator'].search.assert_called_once()
            call_args = mock_services['orchestrator'].search.call_args
            assert call_args[0][2] == "semantic"
            
            # Verify: result is formatted string
            assert isinstance(result, str)
            assert "Test Document" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_with_bm25_mode(self, mock_services, sample_results):
        """
        Test that search_documentation uses BM25 mode when specified.
        
        Validates: Requirements 5.1, 5.4
        """
        # Setup
        mock_services['orchestrator'].search = AsyncMock(return_value=sample_results)
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(
                query="test query",
                limit=5,
                search_mode="bm25"
            )
            
            # Verify: orchestrator.search called with bm25 mode
            mock_services['orchestrator'].search.assert_called_once()
            call_args = mock_services['orchestrator'].search.call_args
            assert call_args[0][2] == "bm25"
            
            # Verify: result is formatted string
            assert isinstance(result, str)
            assert "Test Document" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_with_hybrid_mode(self, mock_services, sample_results):
        """
        Test that search_documentation uses hybrid mode when explicitly specified.
        
        Validates: Requirements 5.1, 5.2
        """
        # Setup
        mock_services['orchestrator'].search = AsyncMock(return_value=sample_results)
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(
                query="test query",
                limit=5,
                search_mode="hybrid"
            )
            
            # Verify: orchestrator.search called with hybrid mode
            mock_services['orchestrator'].search.assert_called_once()
            call_args = mock_services['orchestrator'].search.call_args
            assert call_args[0][2] == "hybrid"
            
            # Verify: result is formatted string
            assert isinstance(result, str)
            assert "Test Document" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_with_invalid_mode_returns_error(self, mock_services):
        """
        Test that search_documentation handles invalid search mode gracefully.
        
        Validates: Requirements 5.5
        """
        # Setup: orchestrator raises ValueError for invalid mode
        mock_services['orchestrator'].search = AsyncMock(
            side_effect=ValueError("Invalid search_mode: invalid. Must be one of: semantic, bm25, hybrid")
        )
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(
                query="test query",
                limit=5,
                search_mode="invalid"
            )
            
            # Verify: error message returned
            assert isinstance(result, str)
            assert "Error" in result or "error" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_fallback_to_semantic_when_orchestrator_unavailable(
        self, mock_services, sample_results
    ):
        """
        Test that search_documentation falls back to semantic search when orchestrator is None.
        
        Validates: Requirements 11.1, 11.2
        """
        # Setup
        mock_services['storage'].search = AsyncMock(return_value=sample_results)
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = None  # Orchestrator unavailable
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(query="test query", limit=5)
            
            # Verify: embedding service called
            mock_services['embedding'].generate_embedding.assert_called_once_with("test query")
            
            # Verify: storage service search called
            mock_services['storage'].search.assert_called_once()
            
            # Verify: result is formatted string
            assert isinstance(result, str)
            assert "Test Document" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_respects_limit_parameter(self, mock_services):
        """
        Test that search_documentation respects the limit parameter.
        
        Validates: Requirements 2.4
        """
        # Create more results than limit
        chunks = [
            DocumentChunk(
                text=f"Document {i}",
                metadata=DocumentMetadata(source=f"doc{i}.pdf", title=f"Doc {i}"),
                id=f"doc_{i}",
                timestamp=datetime.now()
            )
            for i in range(10)
        ]
        results = [SearchResult(chunk=chunk, score=0.9 - i * 0.05) for i, chunk in enumerate(chunks)]
        
        # Setup
        mock_services['orchestrator'].search = AsyncMock(return_value=results[:3])
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute with limit=3
            result = await mcp_module.search_documentation(query="test", limit=3)
            
            # Verify: orchestrator called with limit=3
            call_args = mock_services['orchestrator'].search.call_args
            assert call_args[0][1] == 3
            
            # Verify: result contains only 3 documents
            assert result.count("[1]") == 1
            assert result.count("[2]") == 1
            assert result.count("[3]") == 1
            assert result.count("[4]") == 0
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_formats_results_correctly(self, mock_services, sample_results):
        """
        Test that search_documentation formats results with all required fields.
        
        Validates: Requirements 5.3
        """
        # Setup
        mock_services['orchestrator'].search = AsyncMock(return_value=sample_results)
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(query="test", limit=5)
            
            # Verify: result contains required fields
            assert "[1]" in result  # Result number
            assert "Test Document" in result  # Title
            assert "0.95" in result  # Score
            assert "Source:" in result  # Source label
            assert "http://example.com/test.pdf" in result  # URL
            assert "This is a test document" in result  # Content
            
            # Verify: results separated by divider
            assert "---" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self, mock_services):
        """
        Test that search_documentation handles empty results gracefully.
        
        Validates: Requirements 11.3
        """
        # Setup: return empty results
        mock_services['orchestrator'].search = AsyncMock(return_value=[])
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(query="nonexistent", limit=5)
            
            # Verify: appropriate message returned
            assert isinstance(result, str)
            assert "No results found" in result or "no results" in result.lower()
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
    
    @pytest.mark.asyncio
    async def test_search_handles_missing_metadata_gracefully(self, mock_services):
        """
        Test that search_documentation handles missing metadata fields gracefully.
        
        Validates: Requirements 5.3
        """
        # Create result with minimal metadata
        chunk = DocumentChunk(
            text="Document with minimal metadata",
            metadata=DocumentMetadata(),  # Empty metadata
            id="doc_1",
            timestamp=datetime.now()
        )
        results = [SearchResult(chunk=chunk, score=0.85)]
        
        # Setup
        mock_services['orchestrator'].search = AsyncMock(return_value=results)
        
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = mock_services['orchestrator']
            mcp_module.embedding_service = mock_services['embedding']
            mcp_module.storage_service = mock_services['storage']
            
            # Execute
            result = await mcp_module.search_documentation(query="test", limit=5)
            
            # Verify: result is formatted without errors
            assert isinstance(result, str)
            assert "Document with minimal metadata" in result
            assert "0.85" in result
            # Should use "Unknown source" as fallback
            assert "Unknown source" in result or "Source:" in result
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage


class TestMCPServiceValidation:
    """Test service validation in MCP server."""
    
    @pytest.mark.asyncio
    async def test_search_fails_when_services_not_initialized(self):
        """
        Test that search_documentation returns error when services not initialized.
        
        Validates: Requirements 11.3
        """
        # Import module
        import app.mcp_server as mcp_module
        
        # Patch module-level variables
        original_orchestrator = mcp_module.search_orchestrator
        original_embedding = mcp_module.embedding_service
        original_storage = mcp_module.storage_service
        
        try:
            mcp_module.search_orchestrator = None
            mcp_module.embedding_service = None
            mcp_module.storage_service = None
            
            # Execute
            result = await mcp_module.search_documentation(query="test", limit=5)
            
            # Verify: error message returned
            assert isinstance(result, str)
            assert "not initialized" in result.lower() or "error" in result.lower()
        finally:
            # Restore original values
            mcp_module.search_orchestrator = original_orchestrator
            mcp_module.embedding_service = original_embedding
            mcp_module.storage_service = original_storage
