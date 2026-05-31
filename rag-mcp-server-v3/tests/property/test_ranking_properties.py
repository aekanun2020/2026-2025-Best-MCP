"""
Property-based tests for ranking and result ordering.

These tests use hypothesis to verify universal properties across
randomly generated queries and document collections.
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from datetime import datetime

from pyragdoc.core.bm25 import BM25Retriever
from pyragdoc.utils.thai_tokenizer import ThaiTokenizer
from pyragdoc.models.documents import DocumentChunk, DocumentMetadata, SearchResult


# Custom strategies for document generation
@st.composite
def document_chunks(draw, min_words=5, max_words=50):
    """Generate DocumentChunk objects with random text."""
    # Generate random Thai-like text
    thai_words = ['การ', 'แต่งตั้ง', 'ขั้นตอน', 'อำนาจ', 'หน้าที่', 'คณะกรรมการ',
                  'ข้อ', '๒๑', '๒๒', '๒๓', 'ก.พ.ว.', 'มี', 'ใน', 'และ', 'หรือ']
    
    num_words = draw(st.integers(min_value=min_words, max_value=max_words))
    words = [draw(st.sampled_from(thai_words)) for _ in range(num_words)]
    text = ' '.join(words)
    
    doc_id = draw(st.text(min_size=5, max_size=20))
    
    return DocumentChunk(
        text=text,
        metadata=DocumentMetadata(),
        id=doc_id,
        timestamp=datetime.now()
    )


@st.composite
def document_with_terms(draw, required_terms):
    """Generate DocumentChunk that contains specific terms."""
    # Start with required terms
    words = list(required_terms)
    
    # Add some random filler words
    filler_words = ['การ', 'แต่งตั้ง', 'ขั้นตอน', 'อำนาจ', 'หน้าที่', 'คณะกรรมการ']
    num_filler = draw(st.integers(min_value=3, max_value=10))
    words.extend([draw(st.sampled_from(filler_words)) for _ in range(num_filler)])
    
    # Shuffle to make it more natural
    import random
    random.shuffle(words)
    
    text = ' '.join(words)
    doc_id = draw(st.text(min_size=5, max_size=20))
    
    return DocumentChunk(
        text=text,
        metadata=DocumentMetadata(),
        id=doc_id,
        timestamp=datetime.now()
    )


# Feature: hybrid-search-rrf, Property 4: Exact Match Ranking Priority
@pytest.mark.property
@settings(max_examples=100, deadline=1000)
@given(
    query_terms=st.lists(
        st.sampled_from(['ข้อ', '๒๑', 'การแต่งตั้ง', 'อำนาจ', 'ก.พ.ว.']),
        min_size=1,
        max_size=3,
        unique=True
    ),
    num_matching_docs=st.integers(min_value=1, max_value=3),
    num_non_matching_docs=st.integers(min_value=1, max_value=3)
)
def test_exact_match_ranking_priority(query_terms, num_matching_docs, num_non_matching_docs):
    """
    Property 4: Exact Match Ranking Priority
    
    For any query and document collection, documents containing exact term
    matches from the query should rank higher than documents without exact
    matches when using BM25.
    
    Validates: Requirements 1.4, 9.1
    """
    # Create tokenizer and retriever
    tokenizer = ThaiTokenizer()
    retriever = BM25Retriever(tokenizer)
    
    # Create documents with exact matches
    matching_docs = []
    for _ in range(num_matching_docs):
        doc = DocumentChunk(
            text=' '.join(query_terms) + ' การแต่งตั้ง อำนาจ หน้าที่',
            metadata=DocumentMetadata(),
            id=f"match_{_}",
            timestamp=datetime.now()
        )
        matching_docs.append(doc)
    
    # Create documents without exact matches (different terms)
    non_matching_terms = ['คณะกรรมการ', 'ขั้นตอน', 'วิธีการ', 'กระบวนการ']
    non_matching_docs = []
    for _ in range(num_non_matching_docs):
        doc = DocumentChunk(
            text=' '.join(non_matching_terms),
            metadata=DocumentMetadata(),
            id=f"no_match_{_}",
            timestamp=datetime.now()
        )
        non_matching_docs.append(doc)
    
    # Combine all documents
    all_docs = matching_docs + non_matching_docs
    
    # Index documents
    import asyncio
    asyncio.run(retriever.index_documents(all_docs))
    
    # Search with query
    query = ' '.join(query_terms)
    results = asyncio.run(retriever.search(query, limit=len(all_docs)))
    
    # Verify: matching documents should rank higher
    if results:
        # Get scores of matching vs non-matching docs
        matching_scores = [r.score for r in results if r.chunk.id.startswith('match_')]
        non_matching_scores = [r.score for r in results if r.chunk.id.startswith('no_match_')]
        
        if matching_scores and non_matching_scores:
            # The best matching document should score higher than the best non-matching
            assert max(matching_scores) > max(non_matching_scores), \
                f"Matching docs should rank higher. Matching: {matching_scores}, Non-matching: {non_matching_scores}"


# Feature: hybrid-search-rrf, Property 5: Result Sorting and Limiting
@pytest.mark.property
@settings(max_examples=100, deadline=1000)
@given(
    num_docs=st.integers(min_value=5, max_value=20),
    limit=st.integers(min_value=1, max_value=10)
)
def test_bm25_results_ordering(num_docs, limit):
    """
    Property 3/5: Retriever Results Ordering (BM25)
    
    For any BM25 search results, the documents should be sorted in descending
    order by BM25 score, and the number of results should not exceed the
    requested top_n limit.
    
    Validates: Requirements 1.5, 2.4
    """
    # Create tokenizer and retriever
    tokenizer = ThaiTokenizer()
    retriever = BM25Retriever(tokenizer)
    
    # Create documents with varying relevance
    docs = []
    for i in range(num_docs):
        # Some docs will have query terms, some won't
        if i % 2 == 0:
            text = f"ข้อ ๒๑ การแต่งตั้ง document {i}"
        else:
            text = f"คณะกรรมการ ขั้นตอน document {i}"
        
        doc = DocumentChunk(
            text=text,
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(doc)
    
    # Index documents
    import asyncio
    asyncio.run(retriever.index_documents(docs))
    
    # Search
    query = "ข้อ ๒๑ การแต่งตั้ง"
    results = asyncio.run(retriever.search(query, limit=limit))
    
    # Verify: results should be sorted by descending score
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True), \
        f"Results not sorted by descending score: {scores}"
    
    # Verify: number of results should not exceed limit
    assert len(results) <= limit, \
        f"Number of results ({len(results)}) exceeds limit ({limit})"


@pytest.mark.property
@settings(max_examples=100, deadline=1000)
@given(
    num_docs=st.integers(min_value=3, max_value=15),
    limit=st.integers(min_value=1, max_value=10)
)
def test_result_limit_respected(num_docs, limit):
    """
    Property: Result limit is always respected.
    
    For any search with a limit parameter, the number of returned results
    should never exceed that limit.
    
    Validates: Requirements 1.5
    """
    # Create tokenizer and retriever
    tokenizer = ThaiTokenizer()
    retriever = BM25Retriever(tokenizer)
    
    # Create documents
    docs = []
    for i in range(num_docs):
        doc = DocumentChunk(
            text=f"ข้อ ๒๑ การแต่งตั้ง document {i}",
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(doc)
    
    # Index documents
    import asyncio
    asyncio.run(retriever.index_documents(docs))
    
    # Search
    query = "ข้อ ๒๑"
    results = asyncio.run(retriever.search(query, limit=limit))
    
    # Verify: results count <= limit
    assert len(results) <= limit, \
        f"Results count ({len(results)}) exceeds limit ({limit})"


@pytest.mark.property
@settings(max_examples=100, deadline=1000)
@given(
    num_docs=st.integers(min_value=5, max_value=15)
)
def test_scores_in_valid_range(num_docs):
    """
    Property: Scores should be in valid range [0, 1].
    
    For any BM25 search results, normalized scores should be between 0 and 1.
    
    Validates: Requirements 1.5
    """
    # Create tokenizer and retriever
    tokenizer = ThaiTokenizer()
    retriever = BM25Retriever(tokenizer)
    
    # Create documents
    docs = []
    for i in range(num_docs):
        doc = DocumentChunk(
            text=f"ข้อ {i} การแต่งตั้ง document {i}",
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(doc)
    
    # Index documents
    import asyncio
    asyncio.run(retriever.index_documents(docs))
    
    # Search
    query = "ข้อ การแต่งตั้ง"
    results = asyncio.run(retriever.search(query, limit=num_docs))
    
    # Verify: all scores in [0, 1]
    for result in results:
        assert 0.0 <= result.score <= 1.0, \
            f"Score {result.score} out of range [0, 1]"


@pytest.mark.property
@settings(max_examples=100, deadline=1000)
@given(
    num_docs=st.integers(min_value=3, max_value=10)
)
def test_highest_score_for_best_match(num_docs):
    """
    Property: Document with most query term matches gets highest score.
    
    For any query, the document containing the most query terms should
    receive the highest score.
    
    Validates: Requirements 1.4
    """
    # Create tokenizer and retriever
    tokenizer = ThaiTokenizer()
    retriever = BM25Retriever(tokenizer)
    
    query_terms = ['ข้อ', '๒๑', 'การแต่งตั้ง']
    
    # Create documents with varying numbers of query terms
    docs = []
    
    # Best match: contains all query terms multiple times
    best_doc = DocumentChunk(
        text=' '.join(query_terms * 3),
        metadata=DocumentMetadata(),
        id="best_match",
        timestamp=datetime.now()
    )
    docs.append(best_doc)
    
    # Other docs: contain fewer query terms
    for i in range(num_docs - 1):
        # Contains only some query terms
        text = ' '.join(query_terms[:i % len(query_terms) + 1]) + ' อื่นๆ'
        doc = DocumentChunk(
            text=text,
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(doc)
    
    # Index documents
    import asyncio
    asyncio.run(retriever.index_documents(docs))
    
    # Search
    query = ' '.join(query_terms)
    results = asyncio.run(retriever.search(query, limit=num_docs))
    
    # Verify: best match should be first (highest score)
    if results:
        assert results[0].chunk.id == "best_match", \
            f"Best match should rank first, but got: {[r.chunk.id for r in results]}"


# Feature: hybrid-search-rrf, Property 6: Hybrid Search Balance
# Note: This property test requires integration with actual SearchOrchestrator
# and is better tested in integration tests. Placeholder here for completeness.
@pytest.mark.property
@settings(max_examples=50, deadline=2000)
@given(
    num_docs=st.integers(min_value=5, max_value=10)
)
def test_hybrid_search_includes_both_signals(num_docs):
    """
    Property 6: Hybrid Search Balance (Simplified)
    
    For any query containing both exact terms and conceptual meaning,
    hybrid search should ideally include results from both BM25 and
    semantic search in the final ranking.
    
    Note: This is a simplified version. Full testing requires
    integration with actual embedding service and Qdrant.
    
    Validates: Requirements 8.2, 9.3
    """
    # This test verifies the RRF combination logic works correctly
    # Full hybrid search testing is done in integration tests
    
    from pyragdoc.core.rrf import RRFCombiner
    
    # Create mock documents
    docs = []
    for i in range(num_docs):
        doc = DocumentChunk(
            text=f"Document {i} with content",
            metadata=DocumentMetadata(),
            id=f"doc_{i}",
            timestamp=datetime.now()
        )
        docs.append(doc)
    
    # Simulate BM25 results (exact match focus)
    bm25_results = [
        SearchResult(chunk=docs[0], score=1.0),
        SearchResult(chunk=docs[1], score=0.8),
    ]
    
    # Simulate semantic results (meaning focus)
    semantic_results = [
        SearchResult(chunk=docs[2], score=0.9),
        SearchResult(chunk=docs[3], score=0.7),
    ]
    
    # Combine with RRF
    combiner = RRFCombiner(k=60)
    combined = combiner.combine([bm25_results, semantic_results], limit=num_docs)
    
    # Verify: combined results include documents from both sources
    combined_ids = {r.chunk.id for r in combined}
    bm25_ids = {r.chunk.id for r in bm25_results}
    semantic_ids = {r.chunk.id for r in semantic_results}
    
    # At least some results from each source should be present
    assert len(combined_ids & bm25_ids) > 0, "Should include BM25 results"
    assert len(combined_ids & semantic_ids) > 0, "Should include semantic results"
