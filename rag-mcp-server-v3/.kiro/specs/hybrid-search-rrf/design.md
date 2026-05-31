# Design Document: Hybrid Search with RRF

## Overview

This design implements a hybrid search system that combines BM25 (sparse retrieval) and semantic search (dense retrieval) using Reciprocal Rank Fusion (RRF) to provide both exact term matching and semantic understanding. The system maintains full backward compatibility with existing client code while significantly improving retrieval quality for queries containing exact terms like Thai section numbers.

### Key Design Decisions

1. **RRF over Weighted Combination**: RRF is scale-invariant and doesn't require tuning weights for different score ranges
2. **Dual Indexing**: Maintain separate BM25 and vector indices for optimal performance
3. **Default Hybrid Mode**: Automatically use hybrid search unless explicitly configured otherwise
4. **Thai-Aware Tokenization**: Use pythainlp for proper Thai word segmentation
5. **Backward Compatible API**: No changes required to existing client code

## Architecture

The system extends the existing PyRAGDoc MCP server architecture with hybrid search capabilities:

```
┌─────────────────────────────────────────────────────────────┐
│              MCP Server (app/mcp_server.py)                  │
│  @mcp_server.tool()                                          │
│  search_documentation(query, limit, search_mode="hybrid")   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Search Orchestrator (pyragdoc/core/search.py)       │
│  - Route to appropriate retriever(s)                         │
│  - Coordinate parallel execution                             │
│  - Apply RRF fusion for hybrid mode                          │
│  - Graceful degradation on failures                          │
└──────────┬──────────────────────────────────┬───────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────┐          ┌──────────────────────────┐
│   BM25 Retriever     │          │  Semantic Retriever      │
│  (NEW)               │          │  (EXISTING)              │
│  - Thai tokenization │          │  - Qdrant vector search  │
│  - rank-bm25 library │          │  - Ollama embeddings     │
│  - In-memory index   │          │  - Cosine similarity     │
└──────────┬───────────┘          └──────────┬───────────────┘
           │                                  │
           │                                  │
           │         ┌────────────────────────┘
           │         │
           ▼         ▼
┌─────────────────────────────────────────────────────────────┐
│         RRF Combiner (pyragdoc/core/rrf.py)                 │
│  - Merge rankings from multiple retrievers                  │
│  - Calculate RRF scores: 1/(k + rank)                       │
│  - Return unified ranked list                               │
└─────────────────────────────────────────────────────────────┘

Existing Components (No Changes):
┌─────────────────────────────────────────────────────────────┐
│  - EmbeddingService (pyragdoc/core/embedding.py)            │
│  - QdrantService (pyragdoc/core/storage.py)                 │
│  - DocumentChunk, SearchResult (pyragdoc/models/documents.py)│
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**MCP Server (app/mcp_server.py)**:
- Existing FastAPI + SSE transport implementation
- Exposes `search_documentation` tool
- Add optional `search_mode` parameter (default: "hybrid")
- Delegates to SearchOrchestrator

**Search Orchestrator (NEW: pyragdoc/core/search.py)**:
- Entry point for all search requests
- Routes requests based on search_mode parameter
- Executes BM25 and semantic searches in parallel for hybrid mode
- Applies graceful degradation if one retriever fails
- Returns unified SearchResult list

**BM25 Retriever (NEW: pyragdoc/core/bm25.py)**:
- Maintains in-memory inverted index using rank-bm25 library
- Uses Thai tokenizer for text processing
- Calculates BM25 scores (k1=1.5, b=0.75)
- Returns SearchResult objects with scores
- Syncs with Qdrant on document add/remove

**Semantic Retriever (EXISTING: via QdrantService)**:
- Existing QdrantService.search() method
- Generates embeddings for queries via EmbeddingService
- Performs cosine similarity search in Qdrant
- Returns SearchResult objects with similarity scores
- No changes needed to existing implementation

**RRF Combiner (NEW: pyragdoc/core/rrf.py)**:
- Merges multiple ranked SearchResult lists
- Calculates RRF scores using formula: 1/(k + rank)
- Aggregates scores for documents appearing in multiple lists
- Returns final ranked SearchResult list

**Thai Tokenizer (NEW: pyragdoc/utils/thai_tokenizer.py)**:
- Wraps pythainlp for Thai text segmentation
- Preserves Thai numerals, abbreviations, section numbers
- Handles section numbers as single tokens
- Falls back to whitespace tokenization on errors

## Components and Interfaces

### 1. Search Orchestrator (NEW: pyragdoc/core/search.py)

```python
from typing import List, Optional
from ..models.documents import SearchResult

class SearchOrchestrator:
    """Coordinates search across multiple retrievers."""
    
    def __init__(
        self,
        bm25_retriever: 'BM25Retriever',
        storage_service: 'QdrantService',  # Existing semantic retriever
        embedding_service: 'EmbeddingService',  # For semantic search
        rrf_combiner: 'RRFCombiner',
        default_mode: str = "hybrid",
        logger: Optional[logging.Logger] = None
    ):
        self.bm25_retriever = bm25_retriever
        self.storage_service = storage_service
        self.embedding_service = embedding_service
        self.rrf_combiner = rrf_combiner
        self.default_mode = default_mode
        self.logger = logger or get_logger(__name__)
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        search_mode: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Execute search using specified mode.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            search_mode: One of "semantic", "bm25", "hybrid" (default: hybrid)
            
        Returns:
            List of SearchResult objects ranked by relevance
            
        Raises:
            ValueError: If search_mode is invalid
            RuntimeError: If all retrievers fail
        """
        mode = search_mode or self.default_mode
        
        if mode == "semantic":
            return await self._search_semantic(query, limit)
        elif mode == "bm25":
            return await self._search_bm25(query, limit)
        elif mode == "hybrid":
            return await self._search_hybrid(query, limit)
        else:
            raise ValueError(f"Invalid search_mode: {mode}. Must be one of: semantic, bm25, hybrid")
    
    async def _search_semantic(self, query: str, limit: int) -> List[SearchResult]:
        """Execute semantic-only search using existing Qdrant."""
        embedding = await self.embedding_service.generate_embedding(query)
        return await self.storage_service.search(embedding, limit)
    
    async def _search_bm25(self, query: str, limit: int) -> List[SearchResult]:
        """Execute BM25-only search."""
        return await self.bm25_retriever.search(query, limit)
    
    async def _search_hybrid(self, query: str, limit: int) -> List[SearchResult]:
        """Execute hybrid search with graceful degradation."""
        import asyncio
        
        bm25_results = None
        semantic_results = None
        
        # Execute searches in parallel
        try:
            bm25_results = await self.bm25_retriever.search(query, limit * 2)
        except Exception as e:
            self.logger.error(f"BM25 search failed: {e}", exc_info=True)
        
        try:
            embedding = await self.embedding_service.generate_embedding(query)
            semantic_results = await self.storage_service.search(embedding, limit * 2)
        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}", exc_info=True)
        
        # Graceful degradation
        if bm25_results is None and semantic_results is None:
            raise RuntimeError("All retrievers failed")
        elif bm25_results is None:
            self.logger.warning("BM25 failed, using semantic-only results")
            return semantic_results[:limit]
        elif semantic_results is None:
            self.logger.warning("Semantic failed, using BM25-only results")
            return bm25_results[:limit]
        
        # Combine using RRF
        return self.rrf_combiner.combine(
            [bm25_results, semantic_results],
            limit=limit
        )
```

### 2. BM25 Retriever (NEW: pyragdoc/core/bm25.py)

```python
from typing import List, Optional
import logging
from rank_bm25 import BM25Okapi
from ..models.documents import DocumentChunk, SearchResult
from ..utils.thai_tokenizer import ThaiTokenizer
from ..utils.logging import get_logger

class BM25Retriever:
    """BM25-based sparse retrieval with Thai tokenization."""
    
    def __init__(
        self,
        tokenizer: ThaiTokenizer,
        k1: float = 1.5,
        b: float = 0.75,
        logger: Optional[logging.Logger] = None
    ):
        self.tokenizer = tokenizer
        self.k1 = k1
        self.b = b
        self.logger = logger or get_logger(__name__)
        self.index: Optional[BM25Okapi] = None
        self.documents: List[DocumentChunk] = []
    
    async def index_documents(self, documents: List[DocumentChunk]) -> None:
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of DocumentChunk objects to index
        """
        self.documents = documents
        
        # Tokenize all documents
        tokenized_docs = [
            self.tokenizer.tokenize(doc.text)
            for doc in documents
        ]
        
        # Build BM25 index
        self.index = BM25Okapi(tokenized_docs, k1=self.k1, b=self.b)
        self.logger.info(f"Indexed {len(documents)} documents for BM25 search")
    
    async def add_documents(self, documents: List[DocumentChunk]) -> None:
        """
        Add documents to existing index (incremental indexing).
        
        Args:
            documents: List of DocumentChunk objects to add
        """
        self.documents.extend(documents)
        
        # Rebuild index (rank-bm25 doesn't support incremental updates)
        await self.index_documents(self.documents)
    
    async def search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Search using BM25 algorithm.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects with BM25 scores
            
        Raises:
            RuntimeError: If index not built
        """
        if self.index is None:
            raise RuntimeError("BM25 index not built. Call index_documents first.")
        
        # Tokenize query
        query_tokens = self.tokenizer.tokenize(query)
        self.logger.debug(f"Query tokens: {query_tokens}")
        
        # Get BM25 scores
        scores = self.index.get_scores(query_tokens)
        
        # Create results with normalized scores
        results = []
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0
        
        for idx, score in enumerate(scores):
            if score > 0:
                results.append(SearchResult(
                    chunk=self.documents[idx],
                    score=float(score / max_score)
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        self.logger.info(f"BM25 search returned {len(results[:limit])} results")
        return results[:limit]
```

### 3. Thai Tokenizer (NEW: pyragdoc/utils/thai_tokenizer.py)

```python
import re
import logging
from typing import List, Optional
from ..utils.logging import get_logger

class ThaiTokenizer:
    """Thai-aware tokenization with special token preservation."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger(__name__)
        
        # Regex patterns for special tokens
        self.thai_numeral_pattern = re.compile(r'[๐-๙]+')
        self.thai_abbrev_pattern = re.compile(r'[ก-ฮ]\.(?:[ก-ฮ]\.)+')
        self.section_pattern = re.compile(r'ข้อ\s*[๐-๙]+(?:\.[๐-๙]+)*')
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Thai text preserving special tokens.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of tokens
        """
        try:
            # Protect special tokens by replacing with placeholders
            protected_tokens = {}
            protected_text = text
            
            # Protect section numbers (e.g., "ข้อ ๒๑", "๒๑.๑")
            for match in self.section_pattern.finditer(text):
                token = match.group()
                placeholder = f"__SECTION_{len(protected_tokens)}__"
                protected_tokens[placeholder] = token
                protected_text = protected_text.replace(token, placeholder, 1)
            
            # Protect abbreviations (e.g., "ก.พ.ว.")
            for match in self.thai_abbrev_pattern.finditer(protected_text):
                token = match.group()
                placeholder = f"__ABBREV_{len(protected_tokens)}__"
                protected_tokens[placeholder] = token
                protected_text = protected_text.replace(token, placeholder, 1)
            
            # Tokenize using pythainlp
            from pythainlp.tokenize import word_tokenize
            tokens = word_tokenize(protected_text, engine='newmm')
            
            # Restore protected tokens
            restored_tokens = []
            for token in tokens:
                if token in protected_tokens:
                    restored_tokens.append(protected_tokens[token])
                else:
                    restored_tokens.append(token)
            
            return restored_tokens
            
        except Exception as e:
            self.logger.warning(f"Tokenization failed: {e}. Using whitespace fallback.")
            return text.split()
```

### 4. RRF Combiner (NEW: pyragdoc/core/rrf.py)

```python
from typing import List, Dict
import logging
from ..models.documents import SearchResult
from ..utils.logging import get_logger

class RRFCombiner:
    """Reciprocal Rank Fusion for combining multiple rankings."""
    
    def __init__(self, k: int = 60, logger: Optional[logging.Logger] = None):
        """
        Initialize RRF combiner.
        
        Args:
            k: RRF constant (default: 60)
            logger: Logger instance
        """
        self.k = k
        self.logger = logger or get_logger(__name__)
    
    def combine(
        self,
        result_lists: List[List[SearchResult]],
        limit: int
    ) -> List[SearchResult]:
        """
        Combine multiple ranked lists using RRF.
        
        Args:
            result_lists: List of ranked SearchResult lists
            limit: Maximum number of results to return
            
        Returns:
            Combined and re-ranked list of SearchResult objects
        """
        # Calculate RRF scores for each document
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, SearchResult] = {}
        
        for result_list in result_lists:
            for rank, result in enumerate(result_list):
                # Use document ID or text as key
                doc_id = result.chunk.id or result.chunk.text
                rrf_score = 1.0 / (self.k + rank)
                
                if doc_id in rrf_scores:
                    rrf_scores[doc_id] += rrf_score
                else:
                    rrf_scores[doc_id] = rrf_score
                    doc_map[doc_id] = result
        
        # Create combined results
        combined_results = []
        for doc_id, rrf_score in rrf_scores.items():
            result = doc_map[doc_id]
            combined_results.append(SearchResult(
                chunk=result.chunk,
                score=rrf_score
            ))
        
        # Sort by RRF score descending
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        self.logger.info(f"RRF combined {len(result_lists)} result lists into {len(combined_results[:limit])} results")
        return combined_results[:limit]
```

## Data Models

The system uses existing data models from `pyragdoc/models/documents.py`:

```python
# EXISTING - No changes needed
class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    source: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    file_type: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    tags: List[str] = []
    custom: Dict[str, Any] = {}

# EXISTING - No changes needed
class DocumentChunk(BaseModel):
    """A chunk of a document with its content and metadata."""
    text: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    timestamp: datetime = Field(default_factory=datetime.now)
    id: Optional[str] = None

# EXISTING - No changes needed
class SearchResult(BaseModel):
    """Search result with document chunk and score."""
    chunk: DocumentChunk
    score: float
```

No new data models are required. The hybrid search implementation reuses existing models.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: RRF Score Calculation

*For any* set of ranked result lists and any document appearing in those lists, the RRF score should equal the sum of 1/(k + rank_i) across all lists where the document appears, with k=60.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 2: RRF Result Ordering

*For any* combined result list from RRF, the results should be sorted in descending order by RRF score, and limited to the requested top-k value.

**Validates: Requirements 3.4, 3.5**

### Property 3: Thai Token Preservation

*For any* text containing Thai section numbers (e.g., "ข้อ ๒๑"), Thai numerals (๐-๙), or Thai abbreviations (e.g., "ก.พ.ว."), tokenization should preserve these as single tokens without splitting them.

**Validates: Requirements 1.1, 1.2, 4.2, 4.3, 4.4**

### Property 4: Exact Match Ranking Priority

*For any* query and document collection, documents containing exact term matches from the query should rank higher than documents without exact matches when using BM25 or hybrid search.

**Validates: Requirements 1.4, 9.1**

### Property 5: Result Sorting and Limiting

*For any* retriever output (BM25, semantic, or hybrid), results should be sorted by descending score and limited to the requested number of results.

**Validates: Requirements 1.5, 2.4**

### Property 6: Hybrid Search Balance

*For any* query containing both exact terms and conceptual meaning, hybrid search should return results that include both exact matches (from BM25) and semantically similar documents (from semantic search), balanced by RRF scores.

**Validates: Requirements 8.2, 9.3**

### Property 7: Index Synchronization

*For any* document addition or removal operation, both the BM25 index and semantic index should be updated to maintain consistency between document IDs across both indices.

**Validates: Requirements 10.1, 10.2**

### Property 8: Result Format Consistency

*For any* search mode (semantic, bm25, or hybrid), the returned results should follow the same format structure with document content, metadata, score, and rank fields.

**Validates: Requirements 5.3**

## Error Handling

The system implements graceful degradation at multiple levels:

### Retriever-Level Failures

**BM25 Retriever Failure**:
- Log error with full stack trace
- Return empty result list
- Allow orchestrator to fall back to semantic-only search

**Semantic Retriever Failure**:
- Log error with full stack trace
- Return empty result list
- Allow orchestrator to fall back to BM25-only search

**Both Retrievers Fail**:
- Log both errors
- Raise RuntimeError with diagnostic information
- Include error details for debugging

### Tokenization Failures

**Thai Tokenization Failure**:
- Log warning with exception details
- Fall back to whitespace-based tokenization
- Continue processing with degraded tokenization

### Index Corruption

**Corrupted BM25 Index**:
- Detect corruption on load
- Log error and trigger rebuild
- Use semantic search during rebuild

**Corrupted Vector Index**:
- Detect corruption on load
- Log error and trigger rebuild
- Use BM25 search during rebuild

### Invalid Parameters

**Invalid Search Mode**:
- Validate against allowed values: ["semantic", "bm25", "hybrid"]
- Raise ValueError with list of valid options
- Include user-provided value in error message

**Invalid Limit Parameter**:
- Validate limit > 0
- Raise ValueError with constraint description
- Suggest reasonable default value

### Error Logging Strategy

All errors should be logged with:
- Timestamp
- Error level (ERROR for failures, WARNING for degradation)
- Component name (BM25Retriever, SemanticRetriever, etc.)
- Full exception details including stack trace
- Context information (query, parameters, state)

## Testing Strategy

The testing strategy employs a dual approach combining unit tests for specific examples and edge cases with property-based tests for universal correctness properties.

### Unit Testing

Unit tests focus on:
- **Specific examples**: Verify correct behavior for known inputs (e.g., "ข้อ ๒๑" query)
- **Edge cases**: Empty queries, single-word queries, very long queries
- **Error conditions**: Invalid parameters, missing indices, corrupted data
- **Integration points**: Component interactions, API compatibility

**Key Unit Test Areas**:
1. Thai tokenizer with specific section numbers and abbreviations
2. BM25 scoring with known document-query pairs
3. RRF combination with hand-calculated expected scores
4. Search orchestrator mode routing
5. Graceful degradation scenarios
6. API backward compatibility

### Property-Based Testing

Property-based tests use the **hypothesis** library to verify universal properties across randomly generated inputs. Each property test should run a minimum of 100 iterations to ensure comprehensive coverage.

**Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(...)
def test_property_name(...):
    # Feature: hybrid-search-rrf, Property N: [property text]
    pass
```

**Key Property Test Areas**:

1. **RRF Score Calculation** (Property 1)
   - Generate random ranked lists with varying document overlaps
   - Verify RRF formula: score = Σ(1/(60 + rank_i))
   - Test with 0-5 result lists, 0-20 documents per list

2. **RRF Result Ordering** (Property 2)
   - Generate random RRF scores
   - Verify descending sort order
   - Verify limit parameter respected

3. **Thai Token Preservation** (Property 3)
   - Generate random text with Thai numerals, abbreviations, section numbers
   - Verify tokens remain intact after tokenization
   - Test with mixed Thai-English text

4. **Exact Match Ranking** (Property 4)
   - Generate random queries and document collections
   - Verify documents with exact matches rank higher
   - Test with varying numbers of exact matches

5. **Result Sorting and Limiting** (Property 5)
   - Generate random result lists with scores
   - Verify sorting by descending score
   - Verify length matches limit parameter

6. **Hybrid Search Balance** (Property 6)
   - Generate queries with both exact terms and conceptual content
   - Verify results include both BM25 and semantic matches
   - Verify RRF balances both signals

7. **Index Synchronization** (Property 7)
   - Generate random document add/remove operations
   - Verify both indices updated consistently
   - Verify document IDs match across indices

8. **Result Format Consistency** (Property 8)
   - Generate random queries across all search modes
   - Verify result format matches expected structure
   - Verify all required fields present

### Test Data Generation Strategies

**For Thai Text**:
```python
import hypothesis.strategies as st

thai_numerals = st.text(alphabet='๐๑๒๓๔๕๖๗๘๙', min_size=1, max_size=3)
thai_letters = st.text(alphabet='กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรฤลฦวศษสหฬอฮ', min_size=1, max_size=10)
section_numbers = st.builds(
    lambda n: f"ข้อ {n}",
    thai_numerals
)
```

**For Documents**:
```python
@st.composite
def documents(draw):
    content = draw(st.text(min_size=10, max_size=1000))
    doc_id = draw(st.uuids()).hex
    return Document(id=doc_id, content=content, metadata={})
```

**For Search Results**:
```python
@st.composite
def search_results(draw, documents_strategy):
    doc = draw(documents_strategy)
    score = draw(st.floats(min_value=0.0, max_value=1.0))
    rank = draw(st.integers(min_value=0, max_value=100))
    return SearchResult(document=doc, score=score, rank=rank)
```

### Integration Testing

Integration tests verify the complete search pipeline:

1. **End-to-End Search Flow**:
   - Index sample documents
   - Execute searches in all modes
   - Verify results match expected quality

2. **15 Test Questions**:
   - Run all existing test questions
   - Verify 100% pass rate with hybrid search
   - Compare with semantic-only baseline (92.3%)

3. **Performance Benchmarks**:
   - Measure search latency for different collection sizes
   - Compare hybrid vs semantic-only performance
   - Verify <20% performance degradation

4. **Graceful Degradation**:
   - Simulate retriever failures
   - Verify fallback behavior
   - Verify error logging

### Test Organization

```
tests/
├── unit/
│   ├── test_thai_tokenizer.py
│   ├── test_bm25_retriever.py
│   ├── test_semantic_retriever.py
│   ├── test_rrf_combiner.py
│   └── test_search_orchestrator.py
├── property/
│   ├── test_rrf_properties.py
│   ├── test_tokenization_properties.py
│   ├── test_ranking_properties.py
│   └── test_index_properties.py
├── integration/
│   ├── test_search_pipeline.py
│   ├── test_15_questions.py
│   └── test_graceful_degradation.py
└── performance/
    └── test_benchmarks.py
```

### Coverage Goals

- Unit test coverage: >90% for all components
- Property test coverage: All 8 correctness properties
- Integration test coverage: All user-facing scenarios
- Performance test coverage: Key latency and throughput metrics

## Implementation Notes

### File Structure

New files to create:
```
pyragdoc/
├── core/
│   ├── bm25.py          # NEW: BM25Retriever class
│   ├── rrf.py           # NEW: RRFCombiner class
│   └── search.py        # NEW: SearchOrchestrator class
└── utils/
    └── thai_tokenizer.py # NEW: ThaiTokenizer class

tests/
├── unit/
│   ├── test_thai_tokenizer.py
│   ├── test_bm25_retriever.py
│   ├── test_rrf_combiner.py
│   └── test_search_orchestrator.py
├── property/
│   ├── test_rrf_properties.py
│   ├── test_tokenization_properties.py
│   ├── test_ranking_properties.py
│   └── test_index_properties.py
└── integration/
    ├── test_search_pipeline.py
    └── test_graceful_degradation.py
```

Files to modify:
```
app/mcp_server.py        # MODIFY: Update search_documentation tool
main.py                  # MODIFY: Initialize BM25 and SearchOrchestrator
requirements.txt         # MODIFY: Add pythainlp, rank-bm25, hypothesis
```

### Integration with Existing Code

**1. Modify `app/mcp_server.py`**:
```python
# Add search_mode parameter to search_documentation tool
@mcp_server.tool()
async def search_documentation(
    query: str, 
    limit: int = 5,
    search_mode: str = "hybrid"  # NEW parameter
) -> str:
    """Search through stored documentation
    
    Args:
        query: Search query
        limit: Maximum number of results to return (default: 5)
        search_mode: Search mode - "semantic", "bm25", or "hybrid" (default: hybrid)
    """
    # Use SearchOrchestrator instead of direct storage_service.search()
    results = await search_orchestrator.search(query, limit, search_mode)
    # Format results (existing code)
    ...
```

**2. Modify `main.py`**:
```python
# Initialize hybrid search components
from pyragdoc.core.bm25 import BM25Retriever
from pyragdoc.core.rrf import RRFCombiner
from pyragdoc.core.search import SearchOrchestrator
from pyragdoc.utils.thai_tokenizer import ThaiTokenizer

async def initialize_rag_services():
    global embedding_service, storage_service, search_orchestrator
    
    # Existing initialization
    config = load_config()
    embedding_service = create_embedding_service(config["embedding"])
    storage_service = create_storage_service(config["database"])
    
    # NEW: Initialize hybrid search components
    thai_tokenizer = ThaiTokenizer()
    bm25_retriever = BM25Retriever(thai_tokenizer)
    rrf_combiner = RRFCombiner(k=60)
    
    search_orchestrator = SearchOrchestrator(
        bm25_retriever=bm25_retriever,
        storage_service=storage_service,
        embedding_service=embedding_service,
        rrf_combiner=rrf_combiner,
        default_mode="hybrid"
    )
    
    # Initialize storage
    await storage_service.initialize()
    
    # NEW: Build BM25 index from existing Qdrant documents
    await build_bm25_index()
```

**3. Building BM25 Index from Qdrant**:
```python
async def build_bm25_index():
    """Build BM25 index from documents in Qdrant."""
    try:
        # Scroll through all documents in Qdrant
        scroll_results = await asyncio.to_thread(
            storage_service.client.scroll,
            collection_name=storage_service.collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        # Extract DocumentChunks
        points = scroll_results[0] if isinstance(scroll_results, tuple) else scroll_results.points
        chunks = []
        
        for point in points:
            payload = point.payload
            chunk = DocumentChunk(
                text=payload.get("text", ""),
                metadata=DocumentMetadata(**payload.get("metadata", {})),
                timestamp=datetime.fromisoformat(payload.get("timestamp")),
                id=str(point.id)
            )
            chunks.append(chunk)
        
        # Index documents in BM25
        await bm25_retriever.index_documents(chunks)
        logger.info(f"Built BM25 index with {len(chunks)} documents")
        
    except Exception as e:
        logger.error(f"Failed to build BM25 index: {e}", exc_info=True)
```

**4. Sync BM25 on Document Add**:

Modify `add_directory` tool to also index in BM25:
```python
# After storing in Qdrant
await storage_service.add_documents(embeddings, chunks)

# NEW: Also add to BM25 index
await bm25_retriever.add_documents(chunks)
```

### Dependencies

Add to `requirements.txt`:
```
pythainlp>=3.0.0      # Thai tokenization
rank-bm25>=0.2.2      # BM25 implementation
hypothesis>=6.0.0     # Property-based testing (dev dependency)
```

Existing dependencies (no changes):
```
fastapi
uvicorn
qdrant-client
openai
ollama
pydantic
python-dotenv
```
