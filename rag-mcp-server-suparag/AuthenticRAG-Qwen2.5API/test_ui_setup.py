#!/usr/bin/env python3
"""
Quick test script to verify UI setup
ทดสอบว่าระบบพร้อมใช้งาน Web UI หรือไม่
"""

import sys

def test_imports():
    """Test if all required packages are installed"""
    print("🔍 Testing package imports...")
    
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'streamlit': 'Streamlit',
        'opensearchpy': 'OpenSearch',
        'sentence_transformers': 'SentenceTransformers',
        'openai': 'OpenAI',
        'requests': 'Requests',
        'pydantic': 'Pydantic'
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements-ui.txt")
        return False
    
    print("\n✅ All packages installed!")
    return True

def test_opensearch():
    """Test OpenSearch connection"""
    print("\n🔍 Testing OpenSearch connection...")
    
    try:
        from opensearchpy import OpenSearch
        
        client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            timeout=5
        )
        
        if client.ping():
            print("  ✅ OpenSearch is running")
            
            # Check indices
            try:
                count = client.count(index='anthropic-bm25-index')
                doc_count = count['count']
                print(f"  ✅ Found {doc_count} documents indexed")
                
                if doc_count == 0:
                    print("  ⚠️  No documents found. Run: python authenticRAG.py")
                    return True  # Still OK, just needs indexing
                
                return True
            except Exception as e:
                print(f"  ⚠️  Index not found: {e}")
                print("  Run: python authenticRAG.py to create indices")
                return True  # Still OK, just needs indexing
        else:
            print("  ❌ OpenSearch is not responding")
            print("  Start with: brew services start opensearch")
            return False
            
    except Exception as e:
        print(f"  ❌ OpenSearch connection failed: {e}")
        print("  Make sure OpenSearch is installed and running")
        return False

def test_api_key():
    """Test API key configuration"""
    print("\n🔍 Testing API key configuration...")
    
    import os
    
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    
    if api_key:
        print(f"  ✅ API key found in environment: {api_key[:10]}...")
        return True
    else:
        print("  ⚠️  API key not found in environment")
        print("  Using default key from api_server.py")
        print("  To set: export DASHSCOPE_API_KEY='your-key'")
        return True  # Still OK, using default

def test_ports():
    """Test if ports are available"""
    print("\n🔍 Testing port availability...")
    
    import socket
    
    ports = {
        8001: 'FastAPI Backend',
        8501: 'Streamlit Frontend'
    }
    
    all_available = True
    for port, service in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"  ⚠️  Port {port} ({service}) is already in use")
            all_available = False
        else:
            print(f"  ✅ Port {port} ({service}) is available")
    
    return all_available

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AuthenticRAG UI Setup Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test imports
    results.append(("Packages", test_imports()))
    
    # Test OpenSearch
    results.append(("OpenSearch", test_opensearch()))
    
    # Test API key
    results.append(("API Key", test_api_key()))
    
    # Test ports
    results.append(("Ports", test_ports()))
    
    # Summary
    print()
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed! You're ready to start the UI.")
        print()
        print("Start with:")
        print("  ./start_ui.sh")
        print()
        print("Or manually:")
        print("  Terminal 1: python api_server.py")
        print("  Terminal 2: streamlit run streamlit_app.py")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
