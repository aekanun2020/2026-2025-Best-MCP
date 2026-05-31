#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Server for AuthenticRAG
Provides RESTful API endpoints for search and answer generation
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging
import os

# Import existing RAG components
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AuthenticRAG API",
    description="Contextual RAG API with Hybrid Search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
opensearch_client = None
embedding_model = None
qwen_client = None
api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-REDACTED_SET_VIA_ENV")

# Pydantic models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(10, description="Number of results to return", ge=1, le=50)
    final_top_k: int = Field(5, description="Final number of results after RRF", ge=1, le=20)
    sparse_weight: float = Field(0.5, description="Weight for BM25 search", ge=0, le=1)
    dense_weight: float = Field(0.5, description="Weight for vector search", ge=0, le=1)

class SearchResult(BaseModel):
    doc_id: str
    score: float
    content: str
    context: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float

class AnswerRequest(BaseModel):
    query: str = Field(..., description="Question to answer", min_length=1)
    top_k: int = Field(10, description="Number of documents to retrieve", ge=1, le=50)
    final_top_k: int = Field(5, description="Number of documents to use for answer", ge=1, le=20)

class AnswerResponse(BaseModel):
    query: str
    answer: str
    sources: List[SearchResult]
    generation_time: float

class HealthResponse(BaseModel):
    status: str
    opensearch_connected: bool
    model_loaded: bool
    documents_indexed: int
    timestamp: str

# Initialize components
@app.on_event("startup")
async def startup_event():
    """Initialize OpenSearch and embedding model on startup"""
    global opensearch_client, embedding_model, qwen_client
    
    try:
        # Initialize OpenSearch
        opensearch_client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            timeout=30
        )
        logger.info("✓ OpenSearch connected")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('BAAI/bge-m3')
        logger.info("✓ Embedding model loaded")
        
        # Initialize Qwen client (same as working version)
        qwen_client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        logger.info("✓ Qwen client initialized")
        
    except Exception as e:
        logger.error(f"✗ Startup error: {e}")
        raise

def reciprocal_rank_fusion(sparse_results: List, dense_results: List, k: int = 60) -> List[Dict]:
    """Combine BM25 and vector search results using RRF"""
    scores = {}
    
    for rank, result in enumerate(sparse_results, 1):
        doc_id = result['_id']
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    
    for rank, result in enumerate(dense_results, 1):
        doc_id = result['_id']
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    all_docs = {doc['_id']: doc for doc in sparse_results + dense_results}
    
    fused_results = []
    for doc_id, score in sorted_docs:
        if doc_id in all_docs:
            doc = all_docs[doc_id]
            fused_results.append({
                'doc_id': doc_id,
                'score': score,
                'content': doc['_source'].get('content', ''),
                'context': doc['_source'].get('contextualized_content', '')
            })
    
    return fused_results

def hybrid_search(query: str, top_k: int = 10, sparse_weight: float = 0.5, dense_weight: float = 0.5) -> List[Dict]:
    """Perform hybrid search (BM25 + Vector)"""
    try:
        # BM25 search
        sparse_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "contextualized_content"],
                    "type": "best_fields",
                    "boost": sparse_weight
                }
            },
            "size": top_k
        }
        sparse_response = opensearch_client.search(index='anthropic-bm25-index', body=sparse_query)
        sparse_results = sparse_response['hits']['hits']
        
        # Vector search
        query_embedding = embedding_model.encode(query).tolist()
        dense_query = {
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            },
            "size": top_k
        }
        dense_response = opensearch_client.search(index='anthropic-vector-index', body=dense_query)
        dense_results = dense_response['hits']['hits']
        
        # RRF fusion
        fused_results = reciprocal_rank_fusion(sparse_results, dense_results)
        
        return fused_results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

def generate_answer(query: str, documents: List[Dict]) -> str:
    """Generate answer using Qwen API (same as working version)"""
    try:
        # Build context from documents
        context = ""
        for i, doc in enumerate(documents):
            content = doc.get('content', '')
            context_info = doc.get('context', '')
            context += f"Content: {content}\nContext: {context_info}\n\n"
        
        # Truncate if needed
        words = context.split()
        if len(words) * 1.3 > 4000:
            target_words = int(4000 / 1.3)
            context = " ".join(words[:target_words]) + " ...(truncated)"
        
        # Build prompt (same as working version)
        prompt = f"""You are a question answering assistant. Answer the question as truthful and helpful as possible.

Context information:
{context}

Question: {query}"""

        # Call Qwen API (same as working version)
        completion = qwen_client.chat.completions.create(
            model="qwen2.5-32b-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.6
        )
        
        return completion.choices[0].message.content
            
    except Exception as e:
        logger.error(f"Answer generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")

# API Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AuthenticRAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check OpenSearch
        opensearch_connected = opensearch_client.ping()
        
        # Count documents from both indices
        try:
            count_response = opensearch_client.count(index='anthropic-bm25-index')
            doc_count = count_response['count']
        except:
            doc_count = 0
        
        # Check model
        model_loaded = embedding_model is not None
        
        return HealthResponse(
            status="healthy" if opensearch_connected and model_loaded else "unhealthy",
            opensearch_connected=opensearch_connected,
            model_loaded=model_loaded,
            documents_indexed=doc_count,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest):
    """Search for relevant documents"""
    import time
    start_time = time.time()
    
    try:
        results = hybrid_search(
            query=request.query,
            top_k=request.top_k,
            sparse_weight=request.sparse_weight,
            dense_weight=request.dense_weight
        )
        
        # Limit to final_top_k
        results = results[:request.final_top_k]
        
        search_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=[SearchResult(**r) for r in results],
            total_results=len(results),
            search_time=search_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/answer", response_model=AnswerResponse, tags=["Answer"])
async def answer(request: AnswerRequest):
    """Get answer for a question"""
    import time
    start_time = time.time()
    
    try:
        # Search for relevant documents
        results = hybrid_search(query=request.query, top_k=request.top_k)
        top_results = results[:request.final_top_k]
        
        # Generate answer
        answer_text = generate_answer(request.query, top_results)
        
        generation_time = time.time() - start_time
        
        return AnswerResponse(
            query=request.query,
            answer=answer_text,
            sources=[SearchResult(**r) for r in top_results],
            generation_time=generation_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """Get system statistics"""
    try:
        count_response = opensearch_client.count(index='anthropic-bm25-index')
        
        return {
            "total_documents": count_response['count'],
            "bm25_index": "anthropic-bm25-index",
            "vector_index": "anthropic-vector-index",
            "embedding_model": "BAAI/bge-m3",
            "embedding_dimension": 1024
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting AuthenticRAG API Server...")
    print("📚 Documentation: http://localhost:8001/docs")
    print("🔍 API: http://localhost:8001")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
