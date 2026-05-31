"""
Property-based tests for index operations and result format consistency.

These tests use hypothesis to verify universal properties of search
result formatting and index synchronization.
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from pyragdoc.core.search import SearchOrchestrator
from pyragdoc.core.bm25 import BM25Retriever
from pyragdoc.core.rrf import RRFCombiner
from pyragdoc.utils.thai_tokenizer import ThaiTokenizer
from pyragdoc.models.documents import DocumentChunk, DocumentMetadata, SearchResult


# Custom strategies for generating test data
@st.composite
def document_chunks(draw, min_docs=1, max_docs=10):
    """Generate a list of DocumentChunk objects."""
    num_docs = draw(st.integers(min_value=min_docs, max_value=max_docs))
    chunks = []
    
    for i in range(num_docs):
        doc_id = f"doc_{draw(st.integers(min_value=0, max_value=1000))}"
        text = draw(st.text(min_size=20, max_size=200))
        
        chunk = DocumentChunk(
            text=text,
            metadata=DocumentMetadata(
                source=draw(st.text(min_size=5, max_size=20)),
                title=draw(st.text(min_size=5, max_size=50))
            ),
            id=doc_id,
            timestamp=datetime.now()
        )
        chunks.append(chunk)
    
    return chunks


@st.composite
def search_queries(draw):
    """Generate search query strings."""
    # Mix of English, Thai, and mixed queries
    query_type = draw(st.sampled_from(['english', 'thai', 'mixed']))
    
    if query_type == 'english':
        return draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=5, max_size=50))
    elif query_type == 'thai':
        return draw(st.text(alphabet='กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรฤลฦวศษสหฬอฮ ', min_size=5, max_size=50))
    else:
        english = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=3, max_size=25))
        thai = draw(st.text(alphabet='กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรฤลฦวศษสหฬอฮ ', min_size=3, max_size=25))
        return f"{english} {thai}"


# Feature: hybrid-search-rrf, Property 8: Result Format Consistency
@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100, deadline=None)
@given(
    chunks=document_chunks(min_docs=3, max_docs=10),
    query=search_queries(),
    limit=st.integers(min_value=1, max_value=10),
    search_mode=st.sampled_from(['semantic', 'bm25', 'hybrid'])
)
async def test_result_format_consistency(chunks, query, limit, search_mode):
    """
    Property 8: Result Format Consistency
    
    For any search mode (semantic, bm25, or hybrid), the returned results
    should follow the same format structure with document content, metadata,
    score, and all required fields present.
    
    Validates: Requirements 5.3
    """
    # Skip empty queries
    assume(len(query.strip()) > 0)
    
    # Create mock services
    tokenizer = ThaiTokenizer()
    bm25_retriever = BM25Retriever(tokenizer)
    rrf_combiner = RRFCombiner(k=60)
    
    # Mock storage service (semantic search)
    mock_storage = AsyncMock()
    mock_storage.search = AsyncMock(return_value=[
        SearchResult(chunk=chunk, score=max(0.1, 0.9 - i * 0.08))
        for i, chunk in enumerate(chunks[:limit])
    ])
    
    # Mock embedding service
    mock_embedding = AsyncMock()
    mock_embedding.generate_embedding = AsyncMock(return_value=[0.1] * 384)
    
    # Index documents in BM25
    await bm25_retriever.index_documents(chunks)
    
    # Create orchestrator
    orchestrator = SearchOrchestrator(
        bm25_retriever=bm25_retriever,
        storage_service=mock_storage,
        embedding_service=mock_embedding,
        rrf_combiner=rrf_combiner,
        default_mode="hybrid"
    )
    
    # Execute search
    results = await orchestrator.search(query, limit=limit, search_mode=search_mode)
    
    # Verify: results is a list
    assert isinstance(results, list), \
        f"Results should be a list, got {type(results)}"
    
    # Verify: number of results <= limit
    assert len(results) <= limit, \
        f"Number of results ({len(results)}) exceeds limit ({limit})"
    
    # Verify: each result has required structure
    for i, result in enumerate(results):
        # Result should be SearchResult instance
        assert isinstance(result, SearchResult), \
            f"Result {i} should be SearchResult instance, got {type(result)}"
        
        # Result should have chunk field
        assert hasattr(result, 'chunk'), \
            f"Result {i} missing 'chunk' field"
        assert isinstance(result.chunk, DocumentChunk), \
            f"Result {i} chunk should be DocumentChunk, got {type(result.chunk)}"
        
        # Result should have score field
        assert hasattr(result, 'score'), \
            f"Result {i} missing 'score' field"
        assert isinstance(result.score, (int, float)), \
            f"Result {i} score should be numeric, got {type(result.score)}"
        assert 0.0 <= result.score <= 1.0, \
            f"Result {i} score should be in [0, 1], got {result.score}"
        
        # Chunk should have required fields
        assert hasattr(result.chunk, 'text'), \
            f"Result {i} chunk missing 'text' field"
        assert isinstance(result.chunk.text, str), \
            f"Result {i} chunk text should be string"
        assert len(result.chunk.text) > 0, \
            f"Result {i} chunk text should not be empty"
        
        assert hasattr(result.chunk, 'metadata'), \
            f"Result {i} chunk missing 'metadata' field"
        assert isinstance(result.chunk.metadata, DocumentMetadata), \
            f"Result {i} chunk metadata should be DocumentMetadata"
        
        assert hasattr(result.chunk, 'id'), \
            f"Result {i} chunk missing 'id' field"
        
        assert hasattr(result.chunk, 'timestamp'), \
            f"Result {i} chunk missing 'timestamp' field"
        assert isinstance(result.chunk.timestamp, datetime), \
            f"Result {i} chunk timestamp should be datetime"


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100, deadline=None)
@given(
    chunks=document_chunks(min_docs=5, max_docs=15),
    query=search_queries(),
    limit=st.integers(min_value=1, max_value=10)
)
async def test_result_format_consistency_across_modes(chunks, query, limit):
    """
    Property: All search modes return results with identical structure.
    
    For any query, the result format should be identical across all three
    search modes (semantic, bm25, hybrid), even if the actual results differ.
    
    Validates: Requirements 5.3
    """
    # Skip empty queries
    assume(len(query.strip()) > 0)
    
    # Create mock services
    tokenizer = ThaiTokenizer()
    bm25_retriever = BM25Retriever(tokenizer)
    rrf_combiner = RRFCombiner(k=60)
    
    # Mock storage service
    mock_storage = AsyncMock()
    mock_storage.search = AsyncMock(return_value=[
        SearchResult(chunk=chunk, score=0.9 - i * 0.05)
        for i, chunk in enumerate(chunks[:limit])
    ])
    
    # Mock embedding service
    mock_embedding = AsyncMock()
    mock_embedding.generate_embedding = AsyncMock(return_value=[0.1] * 384)
    
    # Index documents in BM25
    await bm25_retriever.index_documents(chunks)
    
    # Create orchestrator
    orchestrator = SearchOrchestrator(
        bm25_retriever=bm25_retriever,
        storage_service=mock_storage,
        embedding_service=mock_embedding,
        rrf_combiner=rrf_combiner,
        default_mode="hybrid"
    )
    
    # Execute search in all modes
    results_semantic = await orchestrator.search(query, limit=limit, search_mode='semantic')
    results_bm25 = await orchestrator.search(query, limit=limit, search_mode='bm25')
    results_hybrid = await orchestrator.search(query, limit=limit, search_mode='hybrid')
    
    # Verify: all modes return lists
    assert isinstance(results_semantic, list)
    assert isinstance(results_bm25, list)
    assert isinstance(results_hybrid, list)
    
    # Verify: all modes respect limit
    assert len(results_semantic) <= limit
    assert len(results_bm25) <= limit
    assert len(results_hybrid) <= limit
    
    # Verify: all modes return SearchResult objects with same structure
    for mode_name, results in [
        ('semantic', results_semantic),
        ('bm25', results_bm25),
        ('hybrid', results_hybrid)
    ]:
        for i, result in enumerate(results):
            assert isinstance(result, SearchResult), \
                f"{mode_name} mode result {i} should be SearchResult"
            assert hasattr(result, 'chunk'), \
                f"{mode_name} mode result {i} missing chunk"
            assert hasattr(result, 'score'), \
                f"{mode_name} mode result {i} missing score"
            assert isinstance(result.chunk, DocumentChunk), \
                f"{mode_name} mode result {i} chunk should be DocumentChunk"
            assert isinstance(result.score, (int, float)), \
                f"{mode_name} mode result {i} score should be numeric"


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100, deadline=None)
@given(
    chunks=document_chunks(min_docs=3, max_docs=10),
    query=search_queries(),
    limit=st.integers(min_value=1, max_value=10)
)
async def test_result_scores_are_normalized(chunks, query, limit):
    """
    Property: All result scores should be normalized to [0, 1] range.
    
    For any search mode, all returned scores should be in the range [0, 1],
    with higher scores indicating better matches.
    
    Validates: Requirements 5.3, 1.5
    """
    # Skip empty queries
    assume(len(query.strip()) > 0)
    
    # Create mock services
    tokenizer = ThaiTokenizer()
    bm25_retriever = BM25Retriever(tokenizer)
    rrf_combiner = RRFCombiner(k=60)
    
    # Mock storage service
    mock_storage = AsyncMock()
    mock_storage.search = AsyncMock(return_value=[
        SearchResult(chunk=chunk, score=0.85 - i * 0.08)
        for i, chunk in enumerate(chunks[:limit])
    ])
    
    # Mock embedding service
    mock_embedding = AsyncMock()
    mock_embedding.generate_embedding = AsyncMock(return_value=[0.1] * 384)
    
    # Index documents in BM25
    await bm25_retriever.index_documents(chunks)
    
    # Create orchestrator
    orchestrator = SearchOrchestrator(
        bm25_retriever=bm25_retriever,
        storage_service=mock_storage,
        embedding_service=mock_embedding,
        rrf_combiner=rrf_combiner,
        default_mode="hybrid"
    )
    
    # Test all modes
    for search_mode in ['semantic', 'bm25', 'hybrid']:
        results = await orchestrator.search(query, limit=limit, search_mode=search_mode)
        
        for i, result in enumerate(results):
            assert 0.0 <= result.score <= 1.0, \
                f"{search_mode} mode result {i} score {result.score} not in [0, 1]"
        
        # Verify: scores are in descending order
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True), \
            f"{search_mode} mode scores not in descending order: {scores}"
