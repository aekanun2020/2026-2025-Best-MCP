"""
Unit tests for search orchestrator.

These tests verify mode routing, graceful degradation, and error handling.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from pyragdoc.core.search import SearchOrchestrator
from pyragdoc.core.bm25 import BM25Retriever
from pyragdoc.core.rrf import RRFCombiner
from pyragdoc.utils.thai_tokenizer import ThaiTokenizer
from pyragdoc.models.documents import DocumentChunk, DocumentMetadata, SearchResult


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    docs = []
    for i in range(5):
        doc = DocumentChunk(
            text=f"Document {i} content",
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(doc)
    return docs


@pytest_asyncio.fixture
async def bm25_retriever(sample_documents):
    """Create a BM25 retriever with indexed documents."""
    tokenizer = ThaiTokenizer()
    retriever = BM25Retriever(tokenizer)
    await retriever.index_documents(sample_documents)
    return retriever


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service."""
    service = Mock()
    service.search = AsyncMock()
    return service


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    service = Mock()
    service.generate_embedding = AsyncMock(return_value=[0.1] * 768)
    return service


@pytest.fixture
def rrf_combiner():
    """Create an RRF combiner."""
    return RRFCombiner(k=60)


@pytest_asyncio.fixture
async def orchestrator(bm25_retriever, mock_storage_service, mock_embedding_service, rrf_combiner):
    """Create a search orchestrator."""
    return SearchOrchestrator(
        bm25_retriever=bm25_retriever,
        storage_service=mock_storage_service,
        embedding_service=mock_embedding_service,
        rrf_combiner=rrf_combiner,
        default_mode="hybrid"
    )


class TestSearchModeRouting:
    """Test search mode routing."""
    
    @pytest.mark.asyncio
    async def test_semantic_mode(self, orchestrator, mock_storage_service, sample_documents):
        """Test semantic-only mode."""
        # Setup mock to return results
        mock_results = [SearchResult(chunk=sample_documents[0], score=0.9)]
        mock_storage_service.search.return_value = mock_results
        
        # Search with semantic mode
        results = await orchestrator.search("test query", limit=5, search_mode="semantic")
        
        # Verify: storage service was called
        assert mock_storage_service.search.called
        assert results == mock_results
    
    @pytest.mark.asyncio
    async def test_bm25_mode(self, orchestrator, sample_documents):
        """Test BM25-only mode."""
        # Search with BM25 mode
        results = await orchestrator.search("Document 0", limit=5, search_mode="bm25")
        
        # Verify: got results from BM25
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_hybrid_mode(self, orchestrator, mock_storage_service, sample_documents):
        """Test hybrid mode."""
        # Setup mock to return results
        mock_results = [SearchResult(chunk=sample_documents[1], score=0.8)]
        mock_storage_service.search.return_value = mock_results
        
        # Search with hybrid mode
        results = await orchestrator.search("Document 0", limit=5, search_mode="hybrid")
        
        # Verify: got combined results
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)


class TestDefaultMode:
    """Test default mode behavior."""
    
    @pytest.mark.asyncio
    async def test_default_mode_is_hybrid(self, orchestrator, mock_storage_service, sample_documents):
        """Test that default mode is hybrid."""
        # Setup mock
        mock_results = [SearchResult(chunk=sample_documents[0], score=0.9)]
        mock_storage_service.search.return_value = mock_results
        
        # Search without specifying mode
        results = await orchestrator.search("test", limit=5)
        
        # Verify: both BM25 and semantic were attempted (hybrid mode)
        assert mock_storage_service.search.called
    
    @pytest.mark.asyncio
    async def test_custom_default_mode(self, bm25_retriever, mock_storage_service, 
                                       mock_embedding_service, rrf_combiner, sample_documents):
        """Test custom default mode."""
        # Create orchestrator with semantic as default
        orch = SearchOrchestrator(
            bm25_retriever=bm25_retriever,
            storage_service=mock_storage_service,
            embedding_service=mock_embedding_service,
            rrf_combiner=rrf_combiner,
            default_mode="semantic"
        )
        
        # Setup mock
        mock_results = [SearchResult(chunk=sample_documents[0], score=0.9)]
        mock_storage_service.search.return_value = mock_results
        
        # Search without mode (should use semantic)
        results = await orch.search("test", limit=5)
        
        # Verify: semantic search was used
        assert mock_storage_service.search.called


class TestInvalidMode:
    """Test invalid mode error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_mode_raises_error(self, orchestrator):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid search_mode"):
            await orchestrator.search("test", limit=5, search_mode="invalid")
    
    @pytest.mark.asyncio
    async def test_error_message_includes_valid_modes(self, orchestrator):
        """Test that error message lists valid modes."""
        try:
            await orchestrator.search("test", limit=5, search_mode="wrong")
        except ValueError as e:
            assert "semantic" in str(e)
            assert "bm25" in str(e)
            assert "hybrid" in str(e)


class TestGracefulDegradation:
    """Test graceful degradation when retrievers fail."""
    
    @pytest.mark.asyncio
    async def test_bm25_fails_uses_semantic(self, mock_storage_service, 
                                            mock_embedding_service, rrf_combiner, sample_documents):
        """Test fallback to semantic when BM25 fails."""
        # Create BM25 retriever that will fail (no index)
        tokenizer = ThaiTokenizer()
        bm25_retriever = BM25Retriever(tokenizer)
        # Don't index documents - will cause failure
        
        orch = SearchOrchestrator(
            bm25_retriever=bm25_retriever,
            storage_service=mock_storage_service,
            embedding_service=mock_embedding_service,
            rrf_combiner=rrf_combiner
        )
        
        # Setup mock semantic results
        mock_results = [SearchResult(chunk=sample_documents[0], score=0.9)]
        mock_storage_service.search.return_value = mock_results
        
        # Search in hybrid mode
        results = await orch.search("test", limit=5, search_mode="hybrid")
        
        # Verify: got semantic results (fallback)
        assert len(results) > 0
        assert results == mock_results[:5]
    
    @pytest.mark.asyncio
    async def test_semantic_fails_uses_bm25(self, bm25_retriever, mock_embedding_service, 
                                            rrf_combiner):
        """Test fallback to BM25 when semantic fails."""
        # Create mock storage that fails
        mock_storage = Mock()
        mock_storage.search = AsyncMock(side_effect=Exception("Qdrant error"))
        
        orch = SearchOrchestrator(
            bm25_retriever=bm25_retriever,
            storage_service=mock_storage,
            embedding_service=mock_embedding_service,
            rrf_combiner=rrf_combiner
        )
        
        # Search in hybrid mode
        results = await orch.search("Document 0", limit=5, search_mode="hybrid")
        
        # Verify: got BM25 results (fallback)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_both_fail_raises_error(self, mock_embedding_service, rrf_combiner):
        """Test that RuntimeError is raised when both retrievers fail."""
        # Create BM25 that fails
        tokenizer = ThaiTokenizer()
        bm25_retriever = BM25Retriever(tokenizer)
        
        # Create storage that fails
        mock_storage = Mock()
        mock_storage.search = AsyncMock(side_effect=Exception("Qdrant error"))
        
        orch = SearchOrchestrator(
            bm25_retriever=bm25_retriever,
            storage_service=mock_storage,
            embedding_service=mock_embedding_service,
            rrf_combiner=rrf_combiner
        )
        
        # Search should raise RuntimeError
        with pytest.raises(RuntimeError, match="All retrievers failed"):
            await orch.search("test", limit=5, search_mode="hybrid")


class TestHybridCombination:
    """Test hybrid search combination."""
    
    @pytest.mark.asyncio
    async def test_hybrid_combines_both_results(self, orchestrator, mock_storage_service, 
                                                sample_documents):
        """Test that hybrid mode combines BM25 and semantic results."""
        # Setup mock semantic results
        mock_results = [
            SearchResult(chunk=sample_documents[1], score=0.8),
            SearchResult(chunk=sample_documents[2], score=0.7)
        ]
        mock_storage_service.search.return_value = mock_results
        
        # Search in hybrid mode
        results = await orchestrator.search("Document 0", limit=5, search_mode="hybrid")
        
        # Verify: got combined results
        assert len(results) > 0
        
        # Results should include documents from both retrievers
        result_ids = {r.chunk.id for r in results}
        # BM25 should find doc_0 (exact match)
        # Semantic mock returns doc_1 and doc_2
        # Combined should have some from each
        assert len(result_ids) >= 2


class TestStats:
    """Test statistics."""
    
    def test_get_stats(self, orchestrator):
        """Test get_stats method."""
        stats = orchestrator.get_stats()
        
        assert "default_mode" in stats
        assert "bm25_stats" in stats
        assert "rrf_stats" in stats
        assert stats["default_mode"] == "hybrid"


class TestSearchParameters:
    """Test search parameter handling."""
    
    @pytest.mark.asyncio
    async def test_limit_parameter_passed_to_retrievers(self, orchestrator, 
                                                        mock_storage_service, sample_documents):
        """Test that limit parameter is passed correctly."""
        # Setup mock
        mock_results = [SearchResult(chunk=sample_documents[0], score=0.9)]
        mock_storage_service.search.return_value = mock_results
        
        # Search with specific limit
        results = await orchestrator.search("test", limit=3, search_mode="hybrid")
        
        # Verify: results respect limit
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_query_parameter_passed_to_retrievers(self, orchestrator, 
                                                        mock_storage_service, sample_documents):
        """Test that query is passed to retrievers."""
        # Setup mock
        mock_results = [SearchResult(chunk=sample_documents[0], score=0.9)]
        mock_storage_service.search.return_value = mock_results
        
        # Search with specific query
        query = "specific test query"
        results = await orchestrator.search(query, limit=5, search_mode="semantic")
        
        # Verify: embedding service was called (for semantic search)
        assert orchestrator.embedding_service.generate_embedding.called
