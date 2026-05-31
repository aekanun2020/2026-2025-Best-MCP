"""
Property-based tests for RRF (Reciprocal Rank Fusion).

These tests use hypothesis to verify universal properties of RRF
score calculation and result combination.
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from datetime import datetime

from pyragdoc.core.rrf import RRFCombiner
from pyragdoc.models.documents import DocumentChunk, DocumentMetadata, SearchResult


# Custom strategies for generating test data
@st.composite
def search_results(draw, min_results=1, max_results=10):
    """Generate a list of SearchResult objects."""
    num_results = draw(st.integers(min_value=min_results, max_value=max_results))
    results = []
    
    for i in range(num_results):
        doc_id = f"doc_{draw(st.integers(min_value=0, max_value=100))}"
        text = draw(st.text(min_size=10, max_size=100))
        score = draw(st.floats(min_value=0.0, max_value=1.0))
        
        chunk = DocumentChunk(
            text=text,
            metadata=DocumentMetadata(),
            id=doc_id,
            timestamp=datetime.now()
        )
        
        result = SearchResult(chunk=chunk, score=score)
        results.append(result)
    
    return results


@st.composite
def multiple_result_lists(draw, min_lists=1, max_lists=5):
    """Generate multiple result lists for RRF combination."""
    num_lists = draw(st.integers(min_value=min_lists, max_value=max_lists))
    result_lists = []
    
    for _ in range(num_lists):
        results = draw(search_results(min_results=0, max_results=10))
        result_lists.append(results)
    
    return result_lists


# Feature: hybrid-search-rrf, Property 1: RRF Score Calculation
@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(
    num_lists=st.integers(min_value=1, max_value=5),
    num_docs=st.integers(min_value=1, max_value=10),
    k=st.integers(min_value=10, max_value=100)
)
def test_rrf_score_calculation(num_lists, num_docs, k):
    """
    Property 1: RRF Score Calculation
    
    For any document appearing in one or more ranked lists, the RRF score
    should equal the sum of 1/(k + rank_i) for each list where the document
    appears, with k=60 and rank_i being the 1-indexed rank in list i.
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    combiner = RRFCombiner(k=k)
    
    # Create documents
    docs = []
    for i in range(num_docs):
        chunk = DocumentChunk(
            text=f"Document {i}",
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(chunk)
    
    # Create result lists with known rankings
    result_lists = []
    doc_ranks = {}  # Track which rank each doc appears at in each list
    
    for list_idx in range(num_lists):
        results = []
        # Randomly select some documents for this list
        import random
        selected_docs = random.sample(docs, k=min(len(docs), random.randint(1, len(docs))))
        
        for rank, doc in enumerate(selected_docs, start=1):
            result = SearchResult(chunk=doc, score=1.0 / rank)
            results.append(result)
            
            # Track rank
            if doc.id not in doc_ranks:
                doc_ranks[doc.id] = []
            doc_ranks[doc.id].append(rank)
        
        result_lists.append(results)
    
    # Combine using RRF
    combined = combiner.combine(result_lists, limit=num_docs)
    
    # Verify RRF scores
    for result in combined:
        doc_id = result.chunk.id
        
        # Calculate expected RRF score
        expected_score = sum(1.0 / (k + rank) for rank in doc_ranks[doc_id])
        
        # Verify score matches (with small tolerance for floating point)
        assert abs(result.score - expected_score) < 1e-10, \
            f"RRF score mismatch for {doc_id}: expected {expected_score}, got {result.score}"


# Feature: hybrid-search-rrf, Property 2: RRF Result Ordering
@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(
    result_lists=multiple_result_lists(min_lists=1, max_lists=5),
    limit=st.integers(min_value=1, max_value=20)
)
def test_rrf_result_ordering(result_lists, limit):
    """
    Property 2: RRF Result Ordering
    
    For any set of rankings combined with RRF, the final results should be
    sorted in descending order by RRF score, and the number of results
    should not exceed the requested limit.
    
    Validates: Requirements 3.4, 3.5
    """
    # Skip if all lists are empty
    assume(any(len(rl) > 0 for rl in result_lists))
    
    combiner = RRFCombiner(k=60)
    
    # Combine results
    combined = combiner.combine(result_lists, limit=limit)
    
    # Verify: results sorted by descending score
    scores = [r.score for r in combined]
    assert scores == sorted(scores, reverse=True), \
        f"Results not sorted by descending score: {scores}"
    
    # Verify: number of results <= limit
    assert len(combined) <= limit, \
        f"Number of results ({len(combined)}) exceeds limit ({limit})"


@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(
    num_docs=st.integers(min_value=2, max_value=10),
    k=st.integers(min_value=10, max_value=100)
)
def test_rrf_document_in_multiple_lists_scores_higher(num_docs, k):
    """
    Property: Documents appearing in multiple lists get higher RRF scores.
    
    For any document appearing in multiple ranked lists, its RRF score
    should be higher than a document appearing in only one list (assuming
    similar ranks).
    
    Validates: Requirements 3.2
    """
    combiner = RRFCombiner(k=k)
    
    # Create documents
    doc_in_both = DocumentChunk(
        text="Document in both lists",
        metadata=DocumentMetadata(),
        id="doc_both",
        timestamp=datetime.now()
    )
    
    doc_in_one = DocumentChunk(
        text="Document in one list",
        metadata=DocumentMetadata(),
        id="doc_one",
        timestamp=datetime.now()
    )
    
    # Create two result lists
    # List 1: both documents at rank 1 and 2
    list1 = [
        SearchResult(chunk=doc_in_both, score=1.0),
        SearchResult(chunk=doc_in_one, score=0.9)
    ]
    
    # List 2: only doc_in_both at rank 1
    list2 = [
        SearchResult(chunk=doc_in_both, score=1.0)
    ]
    
    # Combine
    combined = combiner.combine([list1, list2], limit=10)
    
    # Find scores
    score_both = None
    score_one = None
    for result in combined:
        if result.chunk.id == "doc_both":
            score_both = result.score
        elif result.chunk.id == "doc_one":
            score_one = result.score
    
    # Verify: doc_in_both should have higher score
    assert score_both is not None and score_one is not None
    assert score_both > score_one, \
        f"Document in both lists should score higher: {score_both} vs {score_one}"


@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(
    num_docs=st.integers(min_value=3, max_value=10),
    k=st.integers(min_value=10, max_value=100)
)
def test_rrf_higher_rank_gets_higher_contribution(num_docs, k):
    """
    Property: Higher ranks (lower rank numbers) contribute more to RRF score.
    
    For any document, appearing at rank 1 should contribute more to the
    RRF score than appearing at rank 2, which should contribute more than
    rank 3, etc.
    
    Validates: Requirements 3.1
    """
    combiner = RRFCombiner(k=k)
    
    # Create documents at different ranks
    docs = []
    for i in range(num_docs):
        chunk = DocumentChunk(
            text=f"Document {i}",
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(chunk)
    
    # Create a single result list with all documents
    results = [SearchResult(chunk=doc, score=1.0 / (i + 1)) for i, doc in enumerate(docs)]
    
    # Combine (single list, so RRF scores = 1/(k + rank))
    combined = combiner.combine([results], limit=num_docs)
    
    # Verify: scores decrease with rank
    for i in range(len(combined) - 1):
        assert combined[i].score > combined[i + 1].score, \
            f"Score at rank {i} should be higher than rank {i+1}"


@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(
    result_lists=multiple_result_lists(min_lists=1, max_lists=5)
)
def test_rrf_no_duplicate_documents(result_lists):
    """
    Property: RRF should not return duplicate documents.
    
    For any set of result lists, the combined results should not contain
    duplicate documents (same document ID).
    
    Validates: Requirements 3.2
    """
    # Skip if all lists are empty
    assume(any(len(rl) > 0 for rl in result_lists))
    
    combiner = RRFCombiner(k=60)
    
    # Combine results
    combined = combiner.combine(result_lists, limit=100)
    
    # Verify: no duplicate document IDs
    doc_ids = [r.chunk.id for r in combined if r.chunk.id]
    assert len(doc_ids) == len(set(doc_ids)), \
        f"Found duplicate documents in combined results"


@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(
    k1=st.integers(min_value=10, max_value=100),
    k2=st.integers(min_value=10, max_value=100)
)
def test_rrf_k_parameter_affects_scores(k1, k2):
    """
    Property: Different k values produce different RRF scores.
    
    For any two different k values, the RRF scores should be different
    (unless k1 == k2).
    
    Validates: Requirements 3.1
    """
    assume(k1 != k2)
    
    # Create simple test data
    doc = DocumentChunk(
        text="Test document",
        metadata=DocumentMetadata(),
        id="doc_1",
        timestamp=datetime.now()
    )
    
    results = [SearchResult(chunk=doc, score=1.0)]
    
    # Combine with different k values
    combiner1 = RRFCombiner(k=k1)
    combiner2 = RRFCombiner(k=k2)
    
    combined1 = combiner1.combine([results], limit=10)
    combined2 = combiner2.combine([results], limit=10)
    
    # Verify: scores are different
    assert combined1[0].score != combined2[0].score, \
        f"Different k values should produce different scores"
