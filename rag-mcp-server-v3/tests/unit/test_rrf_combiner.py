"""
Unit tests for RRF combiner.

These tests verify specific examples and edge cases for RRF combination.
"""
import pytest
from datetime import datetime

from pyragdoc.core.rrf import RRFCombiner
from pyragdoc.models.documents import DocumentChunk, DocumentMetadata, SearchResult


@pytest.fixture
def combiner():
    """Create an RRFCombiner instance for testing."""
    return RRFCombiner(k=60)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    docs = []
    for i in range(5):
        doc = DocumentChunk(
            text=f"Document {i} content",
            metadata=DocumentMetadata(section=f"section_{i}"),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(doc)
    return docs


class TestRRFScoreCalculation:
    """Test RRF score calculation with hand-calculated examples."""
    
    def test_single_list_rrf_scores(self, combiner, sample_documents):
        """Test RRF scores with a single result list."""
        # Create a single result list
        results = [
            SearchResult(chunk=sample_documents[0], score=1.0),
            SearchResult(chunk=sample_documents[1], score=0.8),
            SearchResult(chunk=sample_documents[2], score=0.6),
        ]
        
        # Combine
        combined = combiner.combine([results], limit=10)
        
        # With k=60:
        # doc_0 at rank 1: 1/(60+1) = 0.0164
        # doc_1 at rank 2: 1/(60+2) = 0.0161
        # doc_2 at rank 3: 1/(60+3) = 0.0159
        
        assert len(combined) == 3
        assert combined[0].chunk.id == "doc_0"
        assert abs(combined[0].score - 1.0/61) < 1e-10
        assert abs(combined[1].score - 1.0/62) < 1e-10
        assert abs(combined[2].score - 1.0/63) < 1e-10
    
    def test_document_in_both_lists(self, combiner, sample_documents):
        """Test RRF score for document appearing in both lists."""
        # List 1: doc_0 at rank 1, doc_1 at rank 2
        list1 = [
            SearchResult(chunk=sample_documents[0], score=1.0),
            SearchResult(chunk=sample_documents[1], score=0.8),
        ]
        
        # List 2: doc_0 at rank 1, doc_2 at rank 2
        list2 = [
            SearchResult(chunk=sample_documents[0], score=0.9),
            SearchResult(chunk=sample_documents[2], score=0.7),
        ]
        
        # Combine
        combined = combiner.combine([list1, list2], limit=10)
        
        # doc_0 appears in both at rank 1: 1/61 + 1/61 = 2/61
        # doc_1 appears in list1 at rank 2: 1/62
        # doc_2 appears in list2 at rank 2: 1/62
        
        assert len(combined) == 3
        assert combined[0].chunk.id == "doc_0"  # Highest score
        assert abs(combined[0].score - 2.0/61) < 1e-10
    
    def test_document_in_one_list_only(self, combiner, sample_documents):
        """Test RRF score for documents in only one list."""
        # List 1: doc_0, doc_1
        list1 = [
            SearchResult(chunk=sample_documents[0], score=1.0),
            SearchResult(chunk=sample_documents[1], score=0.8),
        ]
        
        # List 2: doc_2, doc_3
        list2 = [
            SearchResult(chunk=sample_documents[2], score=0.9),
            SearchResult(chunk=sample_documents[3], score=0.7),
        ]
        
        # Combine
        combined = combiner.combine([list1, list2], limit=10)
        
        # All documents appear in only one list
        assert len(combined) == 4
        
        # All should have similar scores (1/61 or 1/62)
        for result in combined:
            assert 0.015 < result.score < 0.017


class TestRRFResultOrdering:
    """Test result ordering and limiting."""
    
    def test_results_sorted_by_descending_score(self, combiner, sample_documents):
        """Test that results are sorted by descending RRF score."""
        # Create lists where doc_0 appears in both (higher score)
        list1 = [
            SearchResult(chunk=sample_documents[0], score=1.0),
            SearchResult(chunk=sample_documents[1], score=0.8),
        ]
        
        list2 = [
            SearchResult(chunk=sample_documents[0], score=0.9),
            SearchResult(chunk=sample_documents[2], score=0.7),
        ]
        
        combined = combiner.combine([list1, list2], limit=10)
        
        # Verify descending order
        scores = [r.score for r in combined]
        assert scores == sorted(scores, reverse=True)
    
    def test_limit_parameter_respected(self, combiner, sample_documents):
        """Test that limit parameter is respected."""
        # Create a result list with 5 documents
        results = [
            SearchResult(chunk=doc, score=1.0 / (i + 1))
            for i, doc in enumerate(sample_documents)
        ]
        
        # Test different limits
        for limit in [1, 2, 3, 5]:
            combined = combiner.combine([results], limit=limit)
            assert len(combined) <= limit
    
    def test_limit_larger_than_results(self, combiner, sample_documents):
        """Test limit larger than available results."""
        results = [
            SearchResult(chunk=sample_documents[0], score=1.0),
            SearchResult(chunk=sample_documents[1], score=0.8),
        ]
        
        combined = combiner.combine([results], limit=100)
        
        # Should return all available results
        assert len(combined) == 2


class TestRRFEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_result_lists_raises_error(self, combiner):
        """Test that empty result_lists raises ValueError."""
        with pytest.raises(ValueError, match="result_lists cannot be empty"):
            combiner.combine([], limit=10)
    
    def test_all_empty_lists_returns_empty(self, combiner):
        """Test that all empty lists returns empty result."""
        result = combiner.combine([[], [], []], limit=10)
        assert result == []
    
    def test_invalid_limit_raises_error(self, combiner, sample_documents):
        """Test that invalid limit raises ValueError."""
        results = [SearchResult(chunk=sample_documents[0], score=1.0)]
        
        with pytest.raises(ValueError, match="limit must be > 0"):
            combiner.combine([results], limit=0)
        
        with pytest.raises(ValueError, match="limit must be > 0"):
            combiner.combine([results], limit=-1)
    
    def test_single_empty_list_ignored(self, combiner, sample_documents):
        """Test that empty lists are filtered out."""
        list1 = [SearchResult(chunk=sample_documents[0], score=1.0)]
        list2 = []
        list3 = [SearchResult(chunk=sample_documents[1], score=0.8)]
        
        combined = combiner.combine([list1, list2, list3], limit=10)
        
        # Should combine list1 and list3, ignoring empty list2
        assert len(combined) == 2


class TestRRFDocumentDeduplication:
    """Test document deduplication."""
    
    def test_same_document_in_multiple_lists(self, combiner, sample_documents):
        """Test that same document in multiple lists is deduplicated."""
        # Same document in all three lists
        list1 = [SearchResult(chunk=sample_documents[0], score=1.0)]
        list2 = [SearchResult(chunk=sample_documents[0], score=0.9)]
        list3 = [SearchResult(chunk=sample_documents[0], score=0.8)]
        
        combined = combiner.combine([list1, list2, list3], limit=10)
        
        # Should have only one result (deduplicated)
        assert len(combined) == 1
        assert combined[0].chunk.id == "doc_0"
        
        # Score should be sum of RRF contributions: 3 * (1/61)
        expected_score = 3.0 / 61
        assert abs(combined[0].score - expected_score) < 1e-10
    
    def test_documents_without_id_deduplicated_by_text(self, combiner):
        """Test that documents without ID are deduplicated by text hash."""
        # Create documents without IDs but same text
        doc1 = DocumentChunk(
            text="Same text content",
            metadata=DocumentMetadata(),
            id=None,
            timestamp=datetime.now()
        )
        
        doc2 = DocumentChunk(
            text="Same text content",
            metadata=DocumentMetadata(),
            id=None,
            timestamp=datetime.now()
        )
        
        list1 = [SearchResult(chunk=doc1, score=1.0)]
        list2 = [SearchResult(chunk=doc2, score=0.9)]
        
        combined = combiner.combine([list1, list2], limit=10)
        
        # Should deduplicate based on text hash
        assert len(combined) == 1


class TestRRFParameters:
    """Test RRF parameters."""
    
    def test_custom_k_parameter(self):
        """Test custom k parameter."""
        combiner = RRFCombiner(k=100)
        assert combiner.k == 100
    
    def test_default_k_parameter(self):
        """Test default k parameter."""
        combiner = RRFCombiner()
        assert combiner.k == 60
    
    def test_different_k_produces_different_scores(self, sample_documents):
        """Test that different k values produce different scores."""
        combiner1 = RRFCombiner(k=60)
        combiner2 = RRFCombiner(k=100)
        
        results = [SearchResult(chunk=sample_documents[0], score=1.0)]
        
        combined1 = combiner1.combine([results], limit=10)
        combined2 = combiner2.combine([results], limit=10)
        
        # Scores should be different
        assert combined1[0].score != combined2[0].score


class TestRRFStats:
    """Test RRF statistics."""
    
    def test_get_stats(self, combiner):
        """Test get_stats method."""
        stats = combiner.get_stats()
        
        assert "k" in stats
        assert stats["k"] == 60


class TestRRFMultipleRetrievers:
    """Test RRF with multiple retrievers."""
    
    def test_three_retrievers(self, combiner, sample_documents):
        """Test combining results from three retrievers."""
        # Retriever 1
        list1 = [
            SearchResult(chunk=sample_documents[0], score=1.0),
            SearchResult(chunk=sample_documents[1], score=0.8),
        ]
        
        # Retriever 2
        list2 = [
            SearchResult(chunk=sample_documents[1], score=0.9),
            SearchResult(chunk=sample_documents[2], score=0.7),
        ]
        
        # Retriever 3
        list3 = [
            SearchResult(chunk=sample_documents[0], score=0.95),
            SearchResult(chunk=sample_documents[3], score=0.6),
        ]
        
        combined = combiner.combine([list1, list2, list3], limit=10)
        
        # doc_0 appears in list1 and list3
        # doc_1 appears in list1 and list2
        # doc_2 appears in list2 only
        # doc_3 appears in list3 only
        
        assert len(combined) == 4
        
        # doc_0 and doc_1 should rank higher (appear in 2 lists)
        top_ids = {combined[0].chunk.id, combined[1].chunk.id}
        assert "doc_0" in top_ids
        assert "doc_1" in top_ids
    
    def test_five_retrievers(self, combiner, sample_documents):
        """Test combining results from five retrievers."""
        result_lists = []
        
        for i in range(5):
            results = [
                SearchResult(chunk=sample_documents[i % len(sample_documents)], score=1.0)
            ]
            result_lists.append(results)
        
        combined = combiner.combine(result_lists, limit=10)
        
        # Should handle 5 retrievers without issues
        assert len(combined) > 0
