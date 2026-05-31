#!/usr/bin/env python3
"""
Script to check Qdrant collections and document counts
"""
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import json

async def check_qdrant():
    """Check Qdrant collections and stats"""
    
    # Connect to Qdrant
    print("Connecting to Qdrant at http://localhost:6333...")
    client = QdrantClient(url="http://localhost:6333")
    
    try:
        # Get all collections
        print("\n" + "="*60)
        print("QDRANT COLLECTIONS")
        print("="*60)
        
        collections = client.get_collections()
        
        if not collections.collections:
            print("No collections found in Qdrant")
            return
        
        print(f"\nFound {len(collections.collections)} collection(s):\n")
        
        # Check each collection
        for collection in collections.collections:
            collection_name = collection.name
            print(f"\n📦 Collection: {collection_name}")
            print("-" * 60)
            
            # Get collection info
            info = client.get_collection(collection_name)
            
            # Points count
            points_count = info.points_count
            print(f"   Documents: {points_count:,}")
            
            # Vector config
            if info.config.params.vectors:
                if isinstance(info.config.params.vectors, dict):
                    for vector_name, vector_config in info.config.params.vectors.items():
                        print(f"   Vector '{vector_name}':")
                        print(f"      - Size: {vector_config.size}")
                        print(f"      - Distance: {vector_config.distance}")
                else:
                    print(f"   Vector size: {info.config.params.vectors.size}")
                    print(f"   Distance: {info.config.params.vectors.distance}")
            
            # Get sample documents
            if points_count > 0:
                print(f"\n   📄 Sample documents (first 3):")
                scroll_result = client.scroll(
                    collection_name=collection_name,
                    limit=3,
                    with_payload=True,
                    with_vectors=False
                )
                
                points = scroll_result[0] if isinstance(scroll_result, tuple) else scroll_result.points
                
                for i, point in enumerate(points, 1):
                    print(f"\n   Document {i}:")
                    print(f"      ID: {point.id}")
                    
                    # Show payload
                    if point.payload:
                        # Show text preview
                        if 'text' in point.payload:
                            text = point.payload['text']
                            preview = text[:100] + "..." if len(text) > 100 else text
                            print(f"      Text: {preview}")
                        
                        # Show metadata
                        if 'metadata' in point.payload:
                            metadata = point.payload['metadata']
                            if metadata.get('source'):
                                print(f"      Source: {metadata['source']}")
                            if metadata.get('title'):
                                print(f"      Title: {metadata['title']}")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        # Calculate total docs by getting info for each collection
        total_docs = 0
        for collection in collections.collections:
            info = client.get_collection(collection.name)
            total_docs += info.points_count
        
        print(f"Total collections: {len(collections.collections)}")
        print(f"Total documents: {total_docs:,}")
        
        # Estimate memory for BM25
        if total_docs > 0:
            print(f"\n💡 BM25 Index Estimates:")
            print(f"   - Documents to index: {total_docs:,}")
            print(f"   - Estimated memory: ~{total_docs * 0.001:.1f} MB")
            print(f"   - Estimated build time: ~{total_docs * 0.01:.1f} seconds")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Qdrant is running:")
        print("  docker-compose ps qdrant")
        print("  docker-compose logs qdrant")

if __name__ == "__main__":
    asyncio.run(check_qdrant())
