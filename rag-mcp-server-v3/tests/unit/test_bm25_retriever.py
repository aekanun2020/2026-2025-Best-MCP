"""
Unit tests for BM25 retriever.

These tests verify specific examples and edge cases for BM25 retrieval.
"""
import pytest
from datetime import datetime

from pyragdoc.core.bm25 import BM25Retriever
from pyragdoc.utils.thai_tokenizer import ThaiTokenizer
from pyragdoc.models.documents import DocumentChunk, DocumentMetadata


@pytest.fixture
def tokenizer():
    """Create a ThaiTokenizer instance for testing."""
    return ThaiTokenizer()


@pytest.fixture
def retriever(tokenizer):
    """Create a BM25Retriever instance for testing."""
    return BM25Retriever(tokenizer)


@pytest.fixture
def sample_thai_documents():
    """Create sample Thai documents for testing."""
    docs = [
        DocumentChunk(
            text="ข้อ ๒๑ ขั้นตอนการแต่งตั้ง",
            metadata=DocumentMetadata(section="21"),
            id="doc1",
            timestamp=datetime.now()
        ),
        DocumentChunk(
            text="ข้อ ๒๑.๑ คณะกรรมการมีอำนาจในการแต่งตั้ง",
            metadata=DocumentMetadata(section="21.1"),
            id="doc2",
            timestamp=datetime.now()
        ),
        DocumentChunk(
            text="ข้อ ๒๑.๒ ขั้นตอนการพิจารณา",
            metadata=DocumentMetadata(section="21.2"),
            id="doc3",
            timestamp=datetime.now()
        ),
        DocumentChunk(
            text="ข้อ ๒๒ อำนาจหน้าที่ของคณะกรรมการ",
            metadata=DocumentMetadata(section="22"),
            id="doc4",
            timestamp=datetime.now()
        ),
        DocumentChunk(
            text="ก.พ.ว. มีอำนาจในการแต่งตั้งข้าราชการ",
            metadata=DocumentMetadata(section="other"),
            id="doc5",
            timestamp=datetime.now()
        ),
    ]
    return docs


class TestBM25Indexing:
    """Test BM25 index building."""
    
    @pytest.mark.asyncio
    async def test_index_documents(self, retriever, sample_thai_documents):
        """Test indexing documents."""
        await retriever.index_documents(sample_thai_documents)
        
        assert retriever.index is not None
        assert len(retriever.documents) == len(sample_thai_documents)
    
    @pytest.mark.asyncio
    async def test_index_empty_documents_raises_error(self, retriever):
        """Test that indexing empty list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot index empty document list"):
            await retriever.index_documents([])
    
    @pytest.mark.asyncio
    async def test_add_documents(self, retriever, sample_thai_documents):
        """Test adding documents to existing index."""
        # Index initial documents
        initial_docs = sample_thai_documents[:3]
        await retriever.index_documents(initial_docs)
        
        # Add more documents
        new_docs = sample_thai_documents[3:]
        await retriever.add_documents(new_docs)
        
        assert len(retriever.documents) == len(sample_thai_documents)
    
    @pytest.mark.asyncio
    async def test_add_empty_documents_raises_error(self, retriever, sample_thai_documents):
        """Test that adding empty list raises ValueError."""
        await retriever.index_documents(sample_thai_documents)
        
        with pytest.raises(ValueError, match="Cannot add empty document list"):
            await retriever.add_documents([])


class TestBM25Search:
    """Test BM25 search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_thai_section_number(self, retriever, sample_thai_documents):
        """Test searching for Thai section number 'ข้อ ๒๑'."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ข้อ ๒๑", limit=5)
        
        # Should return results
        assert len(results) > 0
        
        # Documents with "ข้อ ๒๑" should rank high
        top_result_ids = [r.chunk.id for r in results[:3]]
        assert "doc1" in top_result_ids or "doc2" in top_result_ids or "doc3" in top_result_ids
    
    @pytest.mark.asyncio
    async def test_search_specific_subsection(self, retriever, sample_thai_documents):
        """Test searching for specific subsection 'ข้อ ๒๑.๑'."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ข้อ ๒๑.๑", limit=5)
        
        # Should return results
        assert len(results) > 0
        
        # doc2 (which contains ๒๑.๑) should rank high
        assert results[0].chunk.id == "doc2"
    
    @pytest.mark.asyncio
    async def test_search_thai_abbreviation(self, retriever, sample_thai_documents):
        """Test searching for Thai abbreviation 'ก.พ.ว.'."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ก.พ.ว.", limit=5)
        
        # Should return results
        assert len(results) > 0
        
        # doc5 (which contains ก.พ.ว.) should rank first
        assert results[0].chunk.id == "doc5"
    
    @pytest.mark.asyncio
    async def test_search_keyword(self, retriever, sample_thai_documents):
        """Test searching for keyword 'การแต่งตั้ง'."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("การแต่งตั้ง", limit=5)
        
        # Should return results
        assert len(results) > 0
        
        # Documents containing "การแต่งตั้ง" should rank high
        top_ids = [r.chunk.id for r in results[:3]]
        assert "doc1" in top_ids or "doc2" in top_ids or "doc5" in top_ids
    
    @pytest.mark.asyncio
    async def test_search_multiple_terms(self, retriever, sample_thai_documents):
        """Test searching with multiple terms."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ข้อ ๒๑ การแต่งตั้ง", limit=5)
        
        # Should return results
        assert len(results) > 0
        
        # Documents matching multiple terms should rank higher
        # doc1 and doc2 contain both "ข้อ ๒๑" and "การแต่งตั้ง"
        top_ids = [r.chunk.id for r in results[:2]]
        assert "doc1" in top_ids or "doc2" in top_ids


class TestBM25ScoreNormalization:
    """Test BM25 score normalization."""
    
    @pytest.mark.asyncio
    async def test_scores_normalized_to_one(self, retriever, sample_thai_documents):
        """Test that max score is normalized to 1.0."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ข้อ ๒๑", limit=5)
        
        # Max score should be 1.0
        if results:
            max_score = max(r.score for r in results)
            assert max_score == pytest.approx(1.0, abs=0.01)
    
    @pytest.mark.asyncio
    async def test_scores_in_range(self, retriever, sample_thai_documents):
        """Test that all scores are in [0, 1] range."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ข้อ ๒๑", limit=5)
        
        for result in results:
            assert 0.0 <= result.score <= 1.0
    
    @pytest.mark.asyncio
    async def test_scores_descending(self, retriever, sample_thai_documents):
        """Test that results are sorted by descending score."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ข้อ ๒๑", limit=5)
        
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestBM25Limit:
    """Test limit parameter."""
    
    @pytest.mark.asyncio
    async def test_limit_respected(self, retriever, sample_thai_documents):
        """Test that limit parameter is respected."""
        await retriever.index_documents(sample_thai_documents)
        
        for limit in [1, 2, 3, 5]:
            results = await retriever.search("ข้อ", limit=limit)
            assert len(results) <= limit
    
    @pytest.mark.asyncio
    async def test_limit_larger_than_results(self, retriever, sample_thai_documents):
        """Test limit larger than available results."""
        await retriever.index_documents(sample_thai_documents)
        
        results = await retriever.search("ข้อ ๒๑", limit=100)
        
        # Should return all matching results (not more than indexed docs)
        assert len(results) <= len(sample_thai_documents)


class TestBM25ErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_search_without_index_raises_error(self, retriever):
        """Test that searching without index raises RuntimeError."""
        with pytest.raises(RuntimeError, match="BM25 index not built"):
            await retriever.search("test", limit=5)
    
    @pytest.mark.asyncio
    async def test_search_empty_query_raises_error(self, retriever, sample_thai_documents):
        """Test that empty query raises ValueError."""
        await retriever.index_documents(sample_thai_documents)
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await retriever.search("", limit=5)
    
    @pytest.mark.asyncio
    async def test_search_whitespace_query_raises_error(self, retriever, sample_thai_documents):
        """Test that whitespace-only query raises ValueError."""
        await retriever.index_documents(sample_thai_documents)
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await retriever.search("   ", limit=5)
    
    @pytest.mark.asyncio
    async def test_search_invalid_limit_raises_error(self, retriever, sample_thai_documents):
        """Test that invalid limit raises ValueError."""
        await retriever.index_documents(sample_thai_documents)
        
        with pytest.raises(ValueError, match="Limit must be > 0"):
            await retriever.search("test", limit=0)
        
        with pytest.raises(ValueError, match="Limit must be > 0"):
            await retriever.search("test", limit=-1)
    
    @pytest.mark.asyncio
    async def test_search_no_matching_results(self, retriever, sample_thai_documents):
        """Test search with no matching results."""
        await retriever.index_documents(sample_thai_documents)
        
        # Search for term that doesn't exist
        results = await retriever.search("xyzabc123", limit=5)
        
        # Should return empty list
        assert results == []


class TestBM25Parameters:
    """Test BM25 parameters."""
    
    def test_custom_k1_parameter(self, tokenizer):
        """Test custom k1 parameter."""
        retriever = BM25Retriever(tokenizer, k1=2.0, b=0.75)
        assert retriever.k1 == 2.0
    
    def test_custom_b_parameter(self, tokenizer):
        """Test custom b parameter."""
        retriever = BM25Retriever(tokenizer, k1=1.5, b=0.5)
        assert retriever.b == 0.5
    
    def test_default_parameters(self, tokenizer):
        """Test default parameters."""
        retriever = BM25Retriever(tokenizer)
        assert retriever.k1 == 1.5
        assert retriever.b == 0.75


class TestBM25Stats:
    """Test index statistics."""
    
    @pytest.mark.asyncio
    async def test_get_index_stats_before_indexing(self, retriever):
        """Test stats before indexing."""
        stats = retriever.get_index_stats()
        
        assert stats["num_documents"] == 0
        assert stats["has_index"] is False
        assert stats["k1"] == 1.5
        assert stats["b"] == 0.75
    
    @pytest.mark.asyncio
    async def test_get_index_stats_after_indexing(self, retriever, sample_thai_documents):
        """Test stats after indexing."""
        await retriever.index_documents(sample_thai_documents)
        
        stats = retriever.get_index_stats()
        
        assert stats["num_documents"] == len(sample_thai_documents)
        assert stats["has_index"] is True
