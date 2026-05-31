# SupaRAG Search Architecture

**Document Version:** 1.0  
**Last Updated:** 2026-04-15  
**Status:** Production

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Index Architecture](#index-architecture)
3. [Search Types](#search-types)
4. [Inverted Index Deep Dive](#inverted-index-deep-dive)
5. [BM25 Scoring](#bm25-scoring)
6. [Hybrid Search with RRF](#hybrid-search-with-rrf)
7. [Performance Characteristics](#performance-characteristics)

---

## 🎯 Overview

SupaRAG implements a **Hybrid Search** system that combines:
- **Sparse Search** (BM25) - Keyword-based retrieval using inverted index
- **Dense Search** (Vector) - Semantic retrieval using embeddings
- **RRF Fusion** - Reciprocal Rank Fusion for optimal results

---

## 🏗️ Index Architecture

### Two Separate Indices

SupaRAG uses **two independent OpenSearch indices**:

| Index Name | Purpose | Data Structure | Scoring Method |
|------------|---------|----------------|----------------|
| `anthropic-bm25-index` | Sparse/Keyword Search | Inverted Index | BM25 (Okapi) |
| `anthropic-vector-index` | Dense/Semantic Search | KNN Graph (HNSW) | Cosine Similarity |

---

## 🔍 Search Types

### 1. Sparse Search (BM25)

**Index Used:** `anthropic-bm25-index`

**Code:**
```python
def sparse_search(self, query, k=10):
    """ค้นหาด้วย BM25"""
    response = self.opensearch_client.search(
        index=self.bm25_index_name,  # anthropic-bm25-index
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "contextualized_content"],
                    "type": "best_fields"
                }
            },
            "size": k
        }
    )
    return [(hit["_id"], hit["_score"], hit["_source"]) 
            for hit in response["hits"]["hits"]]
```

**Characteristics:**
- ✅ Uses **Inverted Index**
- ✅ **BM25 Scoring** (Okapi BM25)
- ✅ Searches 2 fields: `content`, `contextualized_content`
- ✅ Query type: `multi_match` with `best_fields`
- ✅ Fast keyword matching: O(1) term lookup

---

### 2. Dense Search (Vector)

**Index Used:** `anthropic-vector-index`

**Code:**
```python
def dense_search(self, query, k=10):
    """ค้นหาด้วย vector similarity"""
    query_embedding = self.encoder.embed_query(query)
    
    response = self.opensearch_client.search(
        index=self.vector_index_name,  # anthropic-vector-index
        body={
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": k
                    }
                }
            },
            "size": k
        }
    )
    return [(hit["_id"], hit["_score"], hit["_source"]) 
            for hit in response["hits"]["hits"]]
```

**Characteristics:**
- ✅ Uses **KNN Graph** (HNSW algorithm)
- ✅ **Cosine Similarity** scoring
- ✅ Semantic search (meaning-based)
- ✅ BGE-M3 embeddings (1024 dimensions)
- ✅ Approximate nearest neighbor search

---

### 3. Hybrid Search (RRF Fusion)

**Indices Used:** Both `anthropic-bm25-index` and `anthropic-vector-index`

**Code:**
```python
def hybrid_search(self, query, k=5, rrf_k=60):
    """ค้นหาแบบ hybrid ด้วย RRF"""
    # 1. Sparse search (BM25)
    sparse_results = self.sparse_search(query, k=k*2)
    
    # 2. Dense search (Vector)
    dense_results = self.dense_search(query, k=k*2)
    
    # 3. RRF Fusion
    rankings = [sparse_results, dense_results]
    fused_results = self.rrf_fusion(rankings, k=rrf_k)
    
    return fused_results[:k]
```

**Characteristics:**
- ✅ Combines **both search methods**
- ✅ **RRF scoring** for optimal ranking
- ✅ Best of both worlds: keyword + semantic
- ✅ More robust than single method

---

## 📊 Inverted Index Deep Dive

### What is an Inverted Index?

An **Inverted Index** is a data structure that maps terms to documents, enabling fast full-text search.

### Index Structure

#### BM25 Index Settings

```python
bm25_settings = {
    "settings": {
        "analysis": {
            "analyzer": {
                "default": {"type": "standard"}
            }
        },
        "similarity": {
            "default": {"type": "BM25"}  # ← BM25 scoring
        },
        "index.queries.cache.enabled": False
    },
    "mappings": {
        "properties": {
            "content": {
                "type": "text",           # ← Creates inverted index
                "analyzer": "standard"
            },
            "contextualized_content": {
                "type": "text",           # ← Creates inverted index
                "analyzer": "standard"
            },
            "doc_id": {"type": "keyword"},
            "chunk_id": {"type": "keyword"},
            "original_index": {
                "type": "integer",
                "index": False            # ← NOT indexed
            }
        }
    }
}
```

### Fields Using Inverted Index

| Field | Type | Analyzer | Inverted Index? | Purpose |
|-------|------|----------|-----------------|---------|
| `content` | `text` | `standard` | ✅ Yes | Original text content |
| `contextualized_content` | `text` | `standard` | ✅ Yes | Content + context |
| `doc_id` | `keyword` | - | ✅ Yes | Document identifier |
| `chunk_id` | `keyword` | - | ✅ Yes | Chunk identifier |
| `original_index` | `integer` | - | ❌ No | Metadata only |

---

## 🔧 How Inverted Index Works

### Example Documents

```
doc_1: "Bearing temperature should not exceed 80°C"
doc_2: "Check bearing condition regularly"
doc_3: "Temperature monitoring is important"
```

### Inverted Index Structure

```
Term          → Document IDs (with positions)
─────────────────────────────────────────────
bearing       → [doc_1:0, doc_2:1]
temperature   → [doc_1:1, doc_3:0]
should        → [doc_1:2]
not           → [doc_1:3]
exceed        → [doc_1:4]
80            → [doc_1:5]
c             → [doc_1:6]
check         → [doc_2:0]
condition     → [doc_2:2]
regularly     → [doc_2:3]
monitoring    → [doc_3:1]
important     → [doc_3:3]
```

### Stored Statistics

For each term, OpenSearch stores:
- **Term Frequency (TF)** - How many times term appears in document
- **Document Frequency (DF)** - How many documents contain the term
- **Positions** - Where term appears in document
- **Field Norms** - Document length normalization

---

## ⚙️ Indexing Process

### 1. Document Indexing

```python
# When adding document to BM25 index
bm25_data = {
    "content": "Bearing temperature should not exceed 80°C",
    "contextualized_content": "This document discusses pump maintenance. Bearing temperature should not exceed 80°C"
}
```

**OpenSearch performs:**

#### Step 1: Tokenization
```
Input:  "Bearing temperature should not exceed 80°C"
Output: ["bearing", "temperature", "should", "not", "exceed", "80", "c"]
```

**Standard Analyzer does:**
- Lowercase conversion
- Remove punctuation
- Split on whitespace
- Unicode normalization

#### Step 2: Build Inverted Index
```
bearing     → doc_0 (position: 0, tf: 1)
temperature → doc_0 (position: 1, tf: 1)
should      → doc_0 (position: 2, tf: 1)
not         → doc_0 (position: 3, tf: 1)
exceed      → doc_0 (position: 4, tf: 1)
80          → doc_0 (position: 5, tf: 1)
c           → doc_0 (position: 6, tf: 1)
```

#### Step 3: Store Statistics
```
Document: doc_0
- Length: 7 tokens
- Field: content
- Norm: 1/√7 ≈ 0.378
```

---

## 🔎 Search Process

### 1. Query Processing

```python
query = "bearing temperature"
```

**OpenSearch performs:**

#### Step 1: Tokenize Query
```
Input:  "bearing temperature"
Output: ["bearing", "temperature"]
```

#### Step 2: Lookup Inverted Index
```
bearing     → [doc_0, doc_5, doc_12]  (df: 3)
temperature → [doc_0, doc_3, doc_8]   (df: 3)
```

#### Step 3: Calculate BM25 Score

For each document, calculate:
```
BM25(doc_0, query) = BM25(doc_0, "bearing") + BM25(doc_0, "temperature")
```

#### Step 4: Rank and Return
```
Results (sorted by score):
1. doc_0: 8.52
2. doc_5: 6.31
3. doc_3: 5.89
...
```

---

## 📐 BM25 Scoring Formula

### Okapi BM25

```
BM25(D, Q) = Σ IDF(qi) × (f(qi, D) × (k1 + 1)) / (f(qi, D) + k1 × (1 - b + b × |D| / avgdl))
```

**Where:**
- `D` = Document
- `Q` = Query
- `qi` = Query term i
- `f(qi, D)` = Term frequency of qi in D (from inverted index)
- `IDF(qi)` = Inverse document frequency (from inverted index)
- `|D|` = Document length (from inverted index)
- `avgdl` = Average document length (from inverted index)
- `k1` = Term frequency saturation parameter (default: 1.2)
- `b` = Length normalization parameter (default: 0.75)

### IDF Calculation

```
IDF(qi) = log((N - df(qi) + 0.5) / (df(qi) + 0.5) + 1)
```

**Where:**
- `N` = Total number of documents
- `df(qi)` = Document frequency of term qi (from inverted index)

### Example Calculation

**Given:**
- Total documents: N = 100
- Query: "bearing temperature"
- Document: doc_0
  - Length: 50 tokens
  - Average doc length: 60 tokens
  - "bearing": tf = 2, df = 10
  - "temperature": tf = 1, df = 15

**Calculate:**

```
IDF("bearing") = log((100 - 10 + 0.5) / (10 + 0.5) + 1) = 2.16

IDF("temperature") = log((100 - 15 + 0.5) / (15 + 0.5) + 1) = 1.87

BM25("bearing") = 2.16 × (2 × 2.2) / (2 + 1.2 × (1 - 0.75 + 0.75 × 50/60))
                = 2.16 × 4.4 / 3.15
                = 3.02

BM25("temperature") = 1.87 × (1 × 2.2) / (1 + 1.2 × (1 - 0.75 + 0.75 × 50/60))
                    = 1.87 × 2.2 / 2.15
                    = 1.91

Total BM25(doc_0) = 3.02 + 1.91 = 4.93
```

---

## 🔀 Hybrid Search with RRF

### Reciprocal Rank Fusion (RRF)

**Formula:**
```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

**Where:**
- `d` = Document
- `rank_i(d)` = Rank of document d in ranker i
- `k` = Constant (default: 60)

### Implementation

```python
def rrf_fusion(self, rankings, k=60):
    """ผสมผลลัพธ์การค้นหาด้วย RRF"""
    fused_scores = {}
    doc_sources = {}
    
    for ranker_id, results in enumerate(rankings):
        for rank, (doc_id, score, source) in enumerate(results):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
                doc_sources[doc_id] = source
            
            # RRF formula: 1 / (k + rank)
            fused_scores[doc_id] += 1.0 / (k + rank)
    
    # Sort by RRF score
    sorted_results = sorted(
        fused_scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    return [(doc_id, score, doc_sources[doc_id]) 
            for doc_id, score in sorted_results]
```

### Example

**Sparse Search Results:**
```
1. doc_5: 8.2  → RRF = 1/(60+0) = 0.0167
2. doc_3: 7.1  → RRF = 1/(60+1) = 0.0164
3. doc_0: 6.5  → RRF = 1/(60+2) = 0.0161
```

**Dense Search Results:**
```
1. doc_0: 0.92 → RRF = 1/(60+0) = 0.0167
2. doc_8: 0.88 → RRF = 1/(60+1) = 0.0164
3. doc_5: 0.85 → RRF = 1/(60+2) = 0.0161
```

**Fused Results:**
```
doc_0: 0.0167 + 0.0161 = 0.0328  ← Rank 1 (appears in both)
doc_5: 0.0167 + 0.0161 = 0.0328  ← Rank 2 (appears in both)
doc_3: 0.0164 + 0      = 0.0164  ← Rank 3 (sparse only)
doc_8: 0      + 0.0164 = 0.0164  ← Rank 4 (dense only)
```

---

## ⚡ Performance Characteristics

### Sparse Search (BM25)

| Metric | Value | Notes |
|--------|-------|-------|
| **Time Complexity** | O(1) term lookup | Via inverted index |
| **Space Complexity** | O(V × D) | V=vocabulary, D=docs |
| **Indexing Speed** | Very Fast | Linear with doc size |
| **Search Speed** | Very Fast | Constant time lookup |
| **Accuracy** | Exact match | Keyword-based |
| **Recall** | Good for keywords | Poor for synonyms |

### Dense Search (Vector)

| Metric | Value | Notes |
|--------|-------|-------|
| **Time Complexity** | O(log N) | Approximate KNN |
| **Space Complexity** | O(N × D) | N=docs, D=dimensions |
| **Indexing Speed** | Moderate | Embedding generation |
| **Search Speed** | Fast | HNSW algorithm |
| **Accuracy** | Semantic match | Meaning-based |
| **Recall** | Good for concepts | Better generalization |

### Hybrid Search (RRF)

| Metric | Value | Notes |
|--------|-------|-------|
| **Time Complexity** | O(sparse + dense) | Both searches |
| **Space Complexity** | O(both indices) | Dual storage |
| **Indexing Speed** | Moderate | Both indices |
| **Search Speed** | Fast | Parallel execution |
| **Accuracy** | Best of both | Combined strengths |
| **Recall** | Highest | Keyword + semantic |

---

## 📈 Comparison Matrix

| Feature | BM25 Index | Vector Index |
|---------|-----------|--------------|
| **Data Structure** | Inverted Index | KNN Graph (HNSW) |
| **Scoring** | BM25 (TF-IDF) | Cosine Similarity |
| **Search Type** | Keyword/Sparse | Semantic/Dense |
| **Query Processing** | Tokenization | Embedding |
| **Lookup Method** | Hash table | Graph traversal |
| **Speed** | Very Fast (O(1)) | Fast (O(log N)) |
| **Accuracy** | Exact keyword match | Semantic similarity |
| **Recall** | Good for exact terms | Good for concepts |
| **Storage** | Terms + positions | Vectors + graph |
| **Index Size** | Moderate | Large |
| **Update Cost** | Low | Moderate |
| **Best For** | Exact queries | Conceptual queries |

---

## 🎯 Summary

### As-Is Architecture

✅ **Sparse Search (BM25)**
- Index: `anthropic-bm25-index`
- Uses: **Inverted Index** (full implementation)
- Scoring: **BM25** (Okapi BM25)
- Fields: `content`, `contextualized_content`
- Analyzer: `standard` (tokenization + lowercase)
- Speed: **Very Fast** (O(1) term lookup)

✅ **Dense Search (Vector)**
- Index: `anthropic-vector-index`
- Uses: **KNN Graph** (HNSW algorithm)
- Scoring: **Cosine Similarity**
- Embeddings: **BGE-M3** (1024 dimensions)
- Speed: **Fast** (approximate nearest neighbor)

✅ **Hybrid Search (RRF)**
- Uses: **Both indices**
- Fusion: **Reciprocal Rank Fusion**
- Result: **Best of both worlds**

### Key Takeaways

1. ✅ **Inverted Index is fully utilized** for BM25 search
2. ✅ **Two separate indices** for different search paradigms
3. ✅ **RRF fusion** combines strengths of both methods
4. ✅ **Production-ready** architecture with proven algorithms
5. ✅ **Scalable** design for large document collections

---

## 📚 References

- [OpenSearch BM25 Documentation](https://opensearch.org/docs/latest/query-dsl/full-text/match/)
- [Okapi BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [Inverted Index Structure](https://nlp.stanford.edu/IR-book/html/htmledition/a-first-take-at-building-an-inverted-index-1.html)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)

---

**Document maintained by:** SupaRAG Team  
**Last reviewed:** 2026-04-15  
**Next review:** 2026-07-15
