# Requirements Document: Hybrid Search with RRF

## Introduction

This document specifies the requirements for implementing Hybrid Search with Reciprocal Rank Fusion (RRF) in the RAG MCP Server. The system currently uses semantic search only, which fails to reliably match exact terms like Thai section numbers (e.g., "ข้อ ๒๑"). The hybrid approach combines BM25 (sparse retrieval) for exact term matching with semantic search (dense retrieval) for meaning-based matching, using RRF to merge results in a scale-invariant manner.

## Glossary

- **RAG_MCP_Server**: The Model Context Protocol server that provides document search functionality
- **BM25**: A sparse retrieval algorithm using term frequency and inverse document frequency for ranking
- **Semantic_Search**: Dense retrieval using vector embeddings and cosine similarity
- **RRF**: Reciprocal Rank Fusion, a scale-invariant algorithm for combining rankings from multiple retrievers
- **Client**: The Adaptive Reasoning Agent (Python) that calls MCP tools
- **Document_Chunk**: A segment of text from the indexed documents with associated metadata
- **Thai_Tokenizer**: A tokenization system for Thai language text (e.g., pythainlp)
- **Search_Mode**: Configuration parameter specifying retrieval strategy (semantic, bm25, or hybrid)
- **BM25_Retriever**: Component that performs sparse retrieval using BM25 algorithm
- **Semantic_Retriever**: Component that performs dense retrieval using vector embeddings
- **RRF_Combiner**: Component that merges results using Reciprocal Rank Fusion algorithm

## Requirements

### Requirement 1: BM25 Sparse Retrieval

**User Story:** As a user searching for exact section numbers in Thai documents, I want the system to match exact terms like "ข้อ ๒๑", so that I can reliably retrieve specific document sections.

#### Acceptance Criteria

1. WHEN a query contains Thai section numbers, THE BM25_Retriever SHALL tokenize the query using Thai-aware tokenization
2. WHEN indexing document chunks, THE BM25_Retriever SHALL preserve section numbers as single tokens (e.g., "๒๑" not split)
3. WHEN calculating BM25 scores, THE BM25_Retriever SHALL use parameters k1=1.5 and b=0.75
4. WHEN a query matches exact terms in a document, THE BM25_Retriever SHALL rank that document higher than documents without exact matches
5. WHEN retrieving results, THE BM25_Retriever SHALL return the top-N ranked documents with their BM25 scores

### Requirement 2: Semantic Dense Retrieval

**User Story:** As a user asking conceptual questions, I want the system to understand meaning and context, so that I can find relevant information even when exact terms don't match.

#### Acceptance Criteria

1. THE Semantic_Retriever SHALL maintain the existing vector embedding functionality
2. WHEN a query is received, THE Semantic_Retriever SHALL generate embeddings using the current embedding model
3. WHEN calculating similarity, THE Semantic_Retriever SHALL use cosine similarity between query and document embeddings
4. WHEN retrieving results, THE Semantic_Retriever SHALL return the top-N ranked documents with their similarity scores
5. THE Semantic_Retriever SHALL continue to work independently when search_mode is "semantic"

### Requirement 3: Reciprocal Rank Fusion

**User Story:** As a system architect, I want to combine BM25 and semantic search results in a scale-invariant way, so that the system benefits from both exact matching and semantic understanding.

#### Acceptance Criteria

1. WHEN combining rankings, THE RRF_Combiner SHALL use the formula: RRF_score = Σ(1 / (k + rank_i)) where k=60
2. WHEN a document appears in both BM25 and semantic results, THE RRF_Combiner SHALL sum the RRF scores from both retrievers
3. WHEN a document appears in only one retriever's results, THE RRF_Combiner SHALL use only that retriever's RRF score
4. WHEN ranking final results, THE RRF_Combiner SHALL sort documents by descending RRF score
5. WHEN the limit parameter is provided, THE RRF_Combiner SHALL return the top-k documents after fusion

### Requirement 4: Thai Language Tokenization

**User Story:** As a developer working with Thai documents, I want proper Thai text tokenization, so that word boundaries and special tokens are correctly identified.

#### Acceptance Criteria

1. WHEN tokenizing Thai text, THE Thai_Tokenizer SHALL use pythainlp or equivalent Thai NLP library
2. WHEN encountering Thai numerals (๐, ๑, ๒, ๓, etc.), THE Thai_Tokenizer SHALL preserve them as single tokens
3. WHEN encountering Thai abbreviations (e.g., ก.พ.ว., ก.ค.ว.), THE Thai_Tokenizer SHALL keep them intact as single tokens
4. WHEN tokenizing section references (e.g., "ข้อ ๒๑"), THE Thai_Tokenizer SHALL preserve the section number as a single token
5. WHEN tokenization fails, THE Thai_Tokenizer SHALL fall back to character-level tokenization

### Requirement 5: API Backward Compatibility

**User Story:** As a client developer, I want the search API to remain unchanged, so that my existing code continues to work without modifications.

#### Acceptance Criteria

1. THE RAG_MCP_Server SHALL maintain the existing tool signature: search_documentation(query: str, limit: int)
2. WHEN the search_documentation tool is called without search_mode parameter, THE RAG_MCP_Server SHALL default to hybrid mode
3. WHEN returning results, THE RAG_MCP_Server SHALL use the same format as the current implementation (list of chunks with scores and metadata)
4. THE RAG_MCP_Server SHALL accept an optional search_mode parameter with values: "semantic", "bm25", or "hybrid"
5. WHEN existing client code calls the tool, THE RAG_MCP_Server SHALL process requests without requiring client code changes

### Requirement 6: Search Mode Configuration

**User Story:** As a developer testing the system, I want to switch between different search modes, so that I can compare performance and debug issues.

#### Acceptance Criteria

1. WHERE search_mode is "semantic", THE RAG_MCP_Server SHALL use only semantic search
2. WHERE search_mode is "bm25", THE RAG_MCP_Server SHALL use only BM25 search
3. WHERE search_mode is "hybrid", THE RAG_MCP_Server SHALL use RRF to combine BM25 and semantic results
4. WHERE search_mode is not provided, THE RAG_MCP_Server SHALL default to "hybrid"
5. WHEN an invalid search_mode is provided, THE RAG_MCP_Server SHALL return an error with valid options

### Requirement 7: Performance Requirements

**User Story:** As a user of the search system, I want fast response times, so that I can get answers quickly without noticeable delays.

#### Acceptance Criteria

1. WHEN processing a typical query, THE RAG_MCP_Server SHALL return results within 100 milliseconds
2. WHEN building the BM25 index, THE RAG_MCP_Server SHALL complete indexing within a reasonable time (one-time cost acceptable)
3. WHEN storing indices in memory, THE RAG_MCP_Server SHALL use reasonable memory (BM25 index + vector index combined)
4. WHEN handling concurrent requests, THE RAG_MCP_Server SHALL maintain response time under 200 milliseconds per request
5. THE RAG_MCP_Server SHALL not degrade performance compared to semantic-only search by more than 20%

### Requirement 8: Exact Section Matching

**User Story:** As a user querying specific regulation sections, I want to retrieve all sub-items of a section, so that I get complete information about that section.

#### Acceptance Criteria

1. WHEN a query contains "ข้อ ๒๑", THE RAG_MCP_Server SHALL return all sub-items (๒๑.๑ through ๒๑.๖) in the top results
2. WHEN a query contains both section number and keywords, THE RAG_MCP_Server SHALL prioritize documents matching both
3. WHEN multiple sections match the query, THE RAG_MCP_Server SHALL rank them by relevance using RRF scores
4. WHEN a section has no exact match, THE RAG_MCP_Server SHALL fall back to semantic similarity
5. THE RAG_MCP_Server SHALL achieve 100% pass rate on the 15 test questions including Q12

### Requirement 9: Result Quality

**User Story:** As a user of the search system, I want high-quality results that balance exact matching with semantic relevance, so that I find the most useful information.

#### Acceptance Criteria

1. WHEN a query has exact term matches, THE RAG_MCP_Server SHALL include those documents in the top results
2. WHEN a query is conceptual without exact matches, THE RAG_MCP_Server SHALL rely on semantic similarity
3. WHEN a query has both exact terms and conceptual meaning, THE RAG_MCP_Server SHALL balance both signals using RRF
4. THE RAG_MCP_Server SHALL maintain or improve the current 92.3% pass rate on test questions
5. THE RAG_MCP_Server SHALL achieve 100% pass rate after implementing hybrid search

### Requirement 10: Index Management

**User Story:** As a system administrator, I want efficient index management, so that the system can handle document updates and maintain search quality.

#### Acceptance Criteria

1. WHEN documents are added to the system, THE RAG_MCP_Server SHALL update both BM25 and semantic indices
2. WHEN documents are removed, THE RAG_MCP_Server SHALL remove entries from both indices
3. WHEN the system starts, THE RAG_MCP_Server SHALL load or build both indices before accepting queries
4. THE RAG_MCP_Server SHALL persist BM25 index to disk for faster startup
5. WHEN indices are corrupted, THE RAG_MCP_Server SHALL rebuild them automatically

### Requirement 11: Error Handling

**User Story:** As a developer, I want clear error messages and graceful degradation, so that I can diagnose issues and maintain system reliability.

#### Acceptance Criteria

1. IF BM25 indexing fails, THEN THE RAG_MCP_Server SHALL log the error and fall back to semantic search only
2. IF semantic search fails, THEN THE RAG_MCP_Server SHALL log the error and fall back to BM25 search only
3. IF both retrievers fail, THEN THE RAG_MCP_Server SHALL return an error message with diagnostic information
4. IF Thai tokenization fails, THEN THE RAG_MCP_Server SHALL fall back to character-level tokenization
5. WHEN errors occur, THE RAG_MCP_Server SHALL include error details in logs for debugging

### Requirement 12: Testing and Validation

**User Story:** As a quality assurance engineer, I want comprehensive tests, so that I can verify the system works correctly across different scenarios.

#### Acceptance Criteria

1. THE RAG_MCP_Server SHALL pass all 15 existing test questions
2. THE RAG_MCP_Server SHALL include unit tests for BM25 retrieval, semantic retrieval, and RRF fusion
3. THE RAG_MCP_Server SHALL include integration tests for the complete search pipeline
4. THE RAG_MCP_Server SHALL include property-based tests for RRF score calculation
5. THE RAG_MCP_Server SHALL include performance benchmarks comparing semantic-only vs hybrid search
