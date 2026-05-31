# Implementation Plan: Hybrid Search with RRF

## Overview

This implementation plan adds hybrid search to the existing PyRAGDoc MCP server. The plan builds incrementally: Thai tokenizer → BM25 retriever → RRF combiner → Search orchestrator → MCP integration. Each component is tested with property-based tests using hypothesis to validate correctness properties.

## Tasks

- [x] 1. Add dependencies and create test structure
  - Add pythainlp, rank-bm25, hypothesis to requirements.txt
  - Create test directories: tests/unit/, tests/property/, tests/integration/
  - Configure pytest if not already configured
  - _Requirements: 12.2_

- [x] 2. Implement Thai Tokenizer
  - [x] 2.1 Create pyragdoc/utils/thai_tokenizer.py with ThaiTokenizer class
    - Implement tokenize() method using pythainlp word_tokenize
    - Add regex patterns for Thai numerals ([๐-๙]+), abbreviations, section numbers
    - Implement token protection/restoration logic with placeholders
    - Add fallback to whitespace tokenization on errors
    - Use existing get_logger() from pyragdoc.utils.logging
    - _Requirements: 4.1, 4.5_
  
  - [x] 2.2 Write property test for Thai token preservation (Property 3)
    - **Property 3: Thai Token Preservation**
    - **Validates: Requirements 1.1, 1.2, 4.2, 4.3, 4.4**
    - File: tests/property/test_tokenization_properties.py
    - Generate random text with Thai numerals, section numbers, abbreviations
    - Verify tokens remain intact after tokenization
    - Use hypothesis with min_examples=100
  
  - [x] 2.3 Write unit tests for Thai tokenizer
    - File: tests/unit/test_thai_tokenizer.py
    - Test specific section numbers: "ข้อ ๒๑", "๒๑.๑"
    - Test abbreviations: "ก.พ.ว.", "ก.ค.ว."
    - Test mixed Thai-English text
    - Test tokenization failure fallback
    - _Requirements: 4.5_

- [x] 3. Implement BM25 Retriever
  - [x] 3.1 Create pyragdoc/core/bm25.py with BM25Retriever class
    - Import rank_bm25.BM25Okapi for indexing
    - Implement __init__ with ThaiTokenizer, k1=1.5, b=0.75
    - Implement index_documents() to build BM25Okapi index
    - Implement add_documents() for incremental indexing (rebuilds index)
    - Implement search() with query tokenization and score normalization
    - Return List[SearchResult] using existing pyragdoc.models.documents.SearchResult
    - Use existing get_logger() from pyragdoc.utils.logging
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 10.1_
  
  - [x] 3.2 Write property test for exact match ranking (Property 4)
    - **Property 4: Exact Match Ranking Priority**
    - **Validates: Requirements 1.4, 9.1**
    - File: tests/property/test_ranking_properties.py
    - Generate random queries and DocumentChunk collections
    - Verify documents with exact matches rank higher
    - Use hypothesis with min_examples=100
  
  - [x] 3.3 Write property test for result sorting and limiting (Property 5)
    - **Property 5: Result Sorting and Limiting**
    - **Validates: Requirements 1.5, 2.4**
    - File: tests/property/test_ranking_properties.py
    - Generate random SearchResult lists with scores
    - Verify descending sort order and limit respected
    - Use hypothesis with min_examples=100
  
  - [x] 3.4 Write unit tests for BM25 retriever
    - File: tests/unit/test_bm25_retriever.py
    - Test indexing with Thai documents
    - Test search with Thai section numbers
    - Test score normalization (max score = 1.0)
    - Test error handling for uninitialized index
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

- [x] 4. Checkpoint - Ensure tokenizer and BM25 tests pass
  - Run: pytest tests/unit/test_thai_tokenizer.py tests/unit/test_bm25_retriever.py
  - Run: pytest tests/property/test_tokenization_properties.py tests/property/test_ranking_properties.py
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement RRF Combiner
  - [x] 5.1 Create pyragdoc/core/rrf.py with RRFCombiner class
    - Implement __init__ with k=60 default parameter
    - Implement combine() method accepting List[List[SearchResult]]
    - Calculate RRF scores: 1/(k + rank) for each document
    - Use chunk.id or chunk.text as document identifier
    - Aggregate scores for documents appearing in multiple lists
    - Return List[SearchResult] sorted by descending RRF score
    - Apply limit parameter to final results
    - Use existing get_logger() from pyragdoc.utils.logging
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 5.2 Write property test for RRF score calculation (Property 1)
    - **Property 1: RRF Score Calculation**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - File: tests/property/test_rrf_properties.py
    - Generate random ranked SearchResult lists with document overlaps
    - Verify RRF formula: score = Σ(1/(60 + rank_i))
    - Test with 0-5 result lists, varying document overlaps
    - Use hypothesis with min_examples=100
  
  - [x] 5.3 Write property test for RRF result ordering (Property 2)
    - **Property 2: RRF Result Ordering**
    - **Validates: Requirements 3.4, 3.5**
    - File: tests/property/test_rrf_properties.py
    - Generate random RRF scores
    - Verify descending sort and limit parameter respected
    - Use hypothesis with min_examples=100
  
  - [x] 5.4 Write unit tests for RRF combiner
    - File: tests/unit/test_rrf_combiner.py
    - Test with hand-calculated RRF scores
    - Test documents in single list only
    - Test documents in multiple lists (score aggregation)
    - Test with empty result lists
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Implement Search Orchestrator
  - [x] 6.1 Create pyragdoc/core/search.py with SearchOrchestrator class
    - Implement __init__ with BM25Retriever, QdrantService, EmbeddingService, RRFCombiner
    - Implement search() method with query, limit, search_mode parameters
    - Validate search_mode: must be "semantic", "bm25", or "hybrid"
    - Implement _search_semantic() using existing storage_service.search()
    - Implement _search_bm25() using bm25_retriever.search()
    - Implement _search_hybrid() with try/except for each retriever
    - Add graceful degradation: if one fails, use the other
    - Raise RuntimeError if both retrievers fail
    - Log all errors with full stack traces
    - Use existing get_logger() from pyragdoc.utils.logging
    - _Requirements: 5.2, 6.1, 6.2, 6.3, 6.4, 11.1, 11.2, 11.3_
  
  - [x] 6.2 Write property test for hybrid search balance (Property 6)
    - **Property 6: Hybrid Search Balance**
    - **Validates: Requirements 8.2, 9.3**
    - File: tests/property/test_ranking_properties.py
    - Generate queries with exact terms and conceptual content
    - Verify results include both BM25 and semantic matches
    - Use hypothesis with min_examples=100
  
  - [x] 6.3 Write unit tests for search orchestrator
    - File: tests/unit/test_search_orchestrator.py
    - Test mode routing: "semantic", "bm25", "hybrid"
    - Test default mode behavior (should be "hybrid")
    - Test invalid mode error handling (ValueError)
    - Test graceful degradation: BM25 fails, semantic succeeds
    - Test graceful degradation: semantic fails, BM25 succeeds
    - Test both fail: RuntimeError raised
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 11.1, 11.2, 11.3_

- [x] 7. Checkpoint - Ensure RRF and orchestrator tests pass
  - Run: pytest tests/unit/test_rrf_combiner.py tests/unit/test_search_orchestrator.py
  - Run: pytest tests/property/test_rrf_properties.py
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Integrate with MCP server
  - [x] 8.1 Modify app/mcp_server.py to add search_mode parameter
    - Add search_mode: str = "hybrid" parameter to search_documentation tool
    - Update tool inputSchema to include search_mode with enum ["semantic", "bm25", "hybrid"]
    - Replace direct storage_service.search() call with search_orchestrator.search()
    - Keep existing result formatting logic unchanged
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.4_
  
  - [x] 8.2 Modify main.py to initialize hybrid search components
    - Import ThaiTokenizer, BM25Retriever, RRFCombiner, SearchOrchestrator
    - Create global search_orchestrator variable
    - In initialize_rag_services(), create ThaiTokenizer instance
    - Create BM25Retriever with tokenizer
    - Create RRFCombiner with k=60
    - Create SearchOrchestrator with all components
    - Update app.rag_services.initialize_services() to include search_orchestrator
    - _Requirements: 5.1, 5.2_
  
  - [x] 8.3 Build BM25 index from existing Qdrant documents
    - Create build_bm25_index() function in main.py
    - Use storage_service.client.scroll() to get all documents from Qdrant
    - Extract DocumentChunk objects from Qdrant payloads
    - Call bm25_retriever.index_documents(chunks)
    - Call build_bm25_index() after storage_service.initialize()
    - Add error handling and logging
    - _Requirements: 10.1, 10.3_
  
  - [x] 8.4 Sync BM25 index on document additions
    - Modify add_directory tool in app/mcp_server.py
    - After storage_service.add_documents(), call bm25_retriever.add_documents()
    - Add error handling: if BM25 fails, log warning but continue
    - _Requirements: 10.1, 10.2_
  
  - [x] 8.5 Write property test for result format consistency (Property 8)
    - **Property 8: Result Format Consistency**
    - **Validates: Requirements 5.3**
    - File: tests/property/test_index_properties.py
    - Generate random queries across all search modes
    - Verify SearchResult format matches expected structure
    - Verify all required fields present (chunk, score)
    - Use hypothesis with min_examples=100
  
  - [x] 8.6 Write unit tests for MCP integration
    - File: tests/unit/test_mcp_integration.py
    - Test search_documentation with no search_mode (should default to hybrid)
    - Test search_documentation with search_mode="semantic"
    - Test search_documentation with search_mode="bm25"
    - Test search_documentation with search_mode="hybrid"
    - Test invalid search_mode returns error
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 9. Checkpoint - Ensure MCP integration works
  - Run: pytest tests/unit/test_mcp_integration.py
  - Run: pytest tests/property/test_index_properties.py
  - Manually test search_documentation tool with all three modes
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Write property test for index synchronization (Property 7)
  - [ ] 10.1 Create tests/property/test_index_properties.py
    - **Property 7: Index Synchronization**
    - **Validates: Requirements 10.1, 10.2**
    - Generate random document add/remove operations
    - Verify both Qdrant and BM25 indices updated consistently
    - Verify document IDs match across indices
    - Use hypothesis with min_examples=100

- [ ] 11. Integration testing
  - [ ] 11.1 Create tests/integration/test_search_pipeline.py
    - Test end-to-end search flow: add documents → search → verify results
    - Test with Thai documents containing section numbers
    - Test hybrid search returns both exact and semantic matches
    - Test graceful degradation scenarios
    - _Requirements: 11.1, 11.2, 11.3, 12.3_
  
  - [ ] 11.2 Create tests/integration/test_15_questions.py
    - Load 15 test questions including Q12 ("ข้อ ๒๑")
    - Index test documents in both Qdrant and BM25
    - Run all questions with hybrid search
    - Measure pass rate (target: 100%)
    - Compare with semantic-only baseline (92.3%)
    - _Requirements: 8.1, 8.5, 9.4, 9.5, 12.1_

- [ ] 12. Final checkpoint - Run full test suite
  - Run: pytest tests/ --cov=pyragdoc --cov-report=term-missing
  - Verify test coverage >90% for new components
  - Verify all 8 correctness properties validated
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 12.2, 12.3, 12.4_

## Notes

- All tasks are required for comprehensive implementation
- Each property test should run minimum 100 iterations using hypothesis
- Property tests should include tag comments: `# Feature: hybrid-search-rrf, Property N: [property text]`
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- All error scenarios should include detailed logging for debugging
- The implementation extends existing PyRAGDoc MCP server without breaking changes
- Existing semantic search continues to work via search_mode="semantic"
- BM25 index is in-memory and rebuilt on startup from Qdrant documents
