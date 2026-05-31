#!/usr/bin/env python3
"""
Demo script to check system readiness without API key
"""

import sys
import os

def check_opensearch():
    """Check if OpenSearch is running"""
    try:
        from opensearchpy import OpenSearch
        client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            use_ssl=False
        )
        info = client.info()
        print(f"✅ OpenSearch is running")
        print(f"   Version: {info['version']['number']}")
        print(f"   Cluster: {info['cluster_name']}")
        return True
    except Exception as e:
        print(f"❌ OpenSearch connection failed: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = [
        'opensearchpy',
        'sentence_transformers',
        'llama_index',
        'openai',
        'langchain',
        'tqdm'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    return len(missing) == 0

def check_api_key():
    """Check if API key is set"""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if api_key:
        print(f"✅ DASHSCOPE_API_KEY is set ({api_key[:10]}...)")
        return True
    else:
        print(f"❌ DASHSCOPE_API_KEY is not set")
        print(f"   Set it with: export DASHSCOPE_API_KEY='your_key'")
        return False

def check_corpus():
    """Check if corpus files exist"""
    corpus_dir = "./corpus_input"
    if not os.path.exists(corpus_dir):
        print(f"❌ Corpus directory not found: {corpus_dir}")
        return False
    
    files = [f for f in os.listdir(corpus_dir) if f.endswith('.md')]
    if files:
        print(f"✅ Found {len(files)} corpus files:")
        for f in files:
            size = os.path.getsize(os.path.join(corpus_dir, f)) / 1024
            print(f"   - {f} ({size:.1f} KB)")
        return True
    else:
        print(f"❌ No .md files found in {corpus_dir}")
        return False

def check_existing_indices():
    """Check if indices already exist"""
    try:
        from opensearchpy import OpenSearch
        client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            use_ssl=False
        )
        
        vector_exists = client.indices.exists(index="anthropic-vector-index")
        bm25_exists = client.indices.exists(index="anthropic-bm25-index")
        
        if vector_exists and bm25_exists:
            print(f"✅ Indices already exist (can use search-only mode)")
            
            # Get document count
            vector_count = client.count(index="anthropic-vector-index")['count']
            bm25_count = client.count(index="anthropic-bm25-index")['count']
            print(f"   - Vector index: {vector_count} documents")
            print(f"   - BM25 index: {bm25_count} documents")
            return True
        else:
            print(f"ℹ️  Indices not found (need to run full indexing)")
            return False
    except Exception as e:
        print(f"⚠️  Could not check indices: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 AuthenticRAG System Check")
    print("=" * 60)
    print()
    
    print("📦 Checking Dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("🔌 Checking OpenSearch...")
    opensearch_ok = check_opensearch()
    print()
    
    print("🔑 Checking API Key...")
    api_key_ok = check_api_key()
    print()
    
    print("📄 Checking Corpus Files...")
    corpus_ok = check_corpus()
    print()
    
    print("🗄️  Checking Existing Indices...")
    indices_exist = check_existing_indices()
    print()
    
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    all_ready = deps_ok and opensearch_ok and api_key_ok and corpus_ok
    
    if all_ready:
        print("✅ System is ready to run!")
        print()
        print("Run with:")
        print("  python authenticRAG.py          # Full indexing + search")
        print("  python onlysearchAuthenticRAG.py  # Search only")
    elif deps_ok and opensearch_ok and corpus_ok and indices_exist:
        print("⚠️  API key not set, but indices exist")
        print()
        print("You can run search-only mode:")
        print("  python onlysearchAuthenticRAG.py")
        print()
        print("To run full system, set API key:")
        print("  export DASHSCOPE_API_KEY='your_key'")
    else:
        print("❌ System is not ready")
        print()
        if not deps_ok:
            print("Install dependencies:")
            print("  pip install -r requirements.txt")
        if not opensearch_ok:
            print("Start OpenSearch (see QUICKSTART.md)")
        if not api_key_ok:
            print("Set API key:")
            print("  export DASHSCOPE_API_KEY='your_key'")
        if not corpus_ok:
            print("Add .md files to corpus_input/")
    
    print()

if __name__ == "__main__":
    main()
