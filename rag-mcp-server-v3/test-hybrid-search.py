#!/usr/bin/env python3
"""
Test script to compare Semantic vs BM25 vs Hybrid search
Especially for queries that need exact matching (sparse search)
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyragdoc.config import load_config
from pyragdoc.core.embedding import create_embedding_service
from pyragdoc.core.storage import create_storage_service
from pyragdoc.utils.thai_tokenizer import ThaiTokenizer
from pyragdoc.core.bm25 import BM25Retriever
from pyragdoc.core.rrf import RRFCombiner
from pyragdoc.core.search import SearchOrchestrator
from pyragdoc.models.documents import DocumentChunk, DocumentMetadata
import datetime

# Test queries that need exact matching (sparse search)
TEST_QUERIES = [
    {
        "query": "ข้อ ๘๖",
        "description": "Thai section number with Thai numeral",
        "expected": "Should find exact section ข้อ ๘๖"
    },
    {
        "query": "๒๑",
        "description": "Thai numeral only",
        "expected": "Should find documents containing ๒๑"
    },
    {
        "query": "ข้อ ๒๑",
        "description": "Section number ข้อ ๒๑",
        "expected": "Should find exact section ข้อ ๒๑"
    },
    {
        "query": "ก.พ.ว.",
        "description": "Thai abbreviation",
        "expected": "Should find documents with ก.พ.ว."
    },
    {
        "query": "การแต่งตั้งตำแหน่งทางวิชาการ",
        "description": "Conceptual query (semantic)",
        "expected": "Should find documents about academic appointments"
    },
    {
        "query": "ข้อ ๘๖ การแต่งตั้ง",
        "description": "Mixed: exact term + concept",
        "expected": "Should find ข้อ ๘๖ AND related to appointments"
    }
]

async def initialize_services():
    """Initialize all services"""
    print("Initializing services...")
    
    config = load_config()
    
    # Initialize embedding and storage
    embedding_service = create_embedding_service(config["embedding"])
    storage_service = create_storage_service(config["database"])
    
    vector_size = embedding_service.get_vector_size()
    storage_service.vector_size = vector_size
    
    await storage_service.initialize()
    
    # Initialize hybrid search components
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
    
    # Build BM25 index
    print("Building BM25 index from Qdrant...")
    scroll_result = await asyncio.to_thread(
        storage_service.client.scroll,
        collection_name=storage_service.collection_name,
        limit=1000,
        with_payload=True,
        with_vectors=False
    )
    
    points = scroll_result[0]
    
    if not points:
        print("❌ No documents found in Qdrant!")
        return None, None, None
    
    # Convert to DocumentChunk
    chunks = []
    for point in points:
        payload = point.payload
        metadata_dict = payload.get("metadata", {})
        metadata = DocumentMetadata(**metadata_dict)
        
        text = payload.get("text", "")
        timestamp_str = payload.get("timestamp")
        timestamp = datetime.datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.datetime.now()
        
        chunk = DocumentChunk(
            text=text,
            metadata=metadata,
            id=str(point.id),
            timestamp=timestamp
        )
        chunks.append(chunk)
    
    await bm25_retriever.index_documents(chunks)
    print(f"✅ BM25 index built with {len(chunks)} documents\n")
    
    return search_orchestrator, embedding_service, storage_service

def format_result(result, rank):
    """Format a single search result"""
    text_preview = result.chunk.text[:150].replace('\n', ' ')
    if len(result.chunk.text) > 150:
        text_preview += "..."
    
    return f"   [{rank}] Score: {result.score:.4f}\n       {text_preview}\n"

async def test_query(query_info, orchestrator, embedding_service, storage_service):
    """Test a single query with all three modes"""
    query = query_info["query"]
    description = query_info["description"]
    expected = query_info["expected"]
    
    print("=" * 80)
    print(f"Query: {query}")
    print(f"Description: {description}")
    print(f"Expected: {expected}")
    print("=" * 80)
    
    # Test 1: Semantic only (old way - dense vectors only)
    print("\n🔵 SEMANTIC ONLY (Dense Vectors):")
    print("-" * 80)
    try:
        semantic_results = await orchestrator.search(query, limit=3, search_mode="semantic")
        if semantic_results:
            for i, result in enumerate(semantic_results, 1):
                print(format_result(result, i))
        else:
            print("   No results found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: BM25 only (new - sparse/keyword matching)
    print("\n🟢 BM25 ONLY (Sparse/Keyword Matching):")
    print("-" * 80)
    try:
        bm25_results = await orchestrator.search(query, limit=3, search_mode="bm25")
        if bm25_results:
            for i, result in enumerate(bm25_results, 1):
                print(format_result(result, i))
        else:
            print("   No results found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Hybrid (best of both worlds)
    print("\n🟣 HYBRID (BM25 + Semantic with RRF):")
    print("-" * 80)
    try:
        hybrid_results = await orchestrator.search(query, limit=3, search_mode="hybrid")
        if hybrid_results:
            for i, result in enumerate(hybrid_results, 1):
                print(format_result(result, i))
        else:
            print("   No results found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n")

async def main():
    """Main test function"""
    print("\n" + "=" * 80)
    print("HYBRID SEARCH TEST - Comparing Semantic vs BM25 vs Hybrid")
    print("=" * 80)
    print("\nThis test compares three search modes:")
    print("  🔵 Semantic: Dense vectors only (old way)")
    print("  🟢 BM25: Sparse/keyword matching (new)")
    print("  🟣 Hybrid: Best of both with RRF fusion")
    print("\n")
    
    # Initialize services
    orchestrator, embedding_service, storage_service = await initialize_services()
    
    if not orchestrator:
        print("Failed to initialize services")
        return
    
    # Run all test queries
    for i, query_info in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(TEST_QUERIES)}")
        print(f"{'='*80}")
        await test_query(query_info, orchestrator, embedding_service, storage_service)
        
        if i < len(TEST_QUERIES):
            input("\nPress Enter to continue to next test...")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)
    print("\n📊 Summary:")
    print("  - Semantic works best for conceptual queries")
    print("  - BM25 works best for exact term matching (Thai numerals, section numbers)")
    print("  - Hybrid combines both for best overall results")
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
