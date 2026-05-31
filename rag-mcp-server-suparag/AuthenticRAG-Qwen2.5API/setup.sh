#!/bin/bash

echo "🚀 Setting up AuthenticRAG System..."
echo ""

# Check if API key is set
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "⚠️  DASHSCOPE_API_KEY is not set!"
    echo ""
    echo "Please set your API key first:"
    echo "  export DASHSCOPE_API_KEY='your_api_key_here'"
    echo ""
    exit 1
fi

echo "✅ API Key found"
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -q opensearchpy sentence-transformers llama-index llama-index-embeddings-huggingface openai tqdm langchain langchain-community

echo ""
echo "✅ Dependencies installed"
echo ""

# Check OpenSearch
echo "🔍 Checking OpenSearch connection..."
curl -s http://localhost:9200 > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ OpenSearch is running"
else
    echo "⚠️  OpenSearch is not running!"
    echo ""
    echo "Please start OpenSearch first. See readme.md for instructions."
    exit 1
fi

echo ""
echo "✨ Setup complete! You can now run:"
echo "  python authenticRAG.py          # Full system (index + search)"
echo "  python onlysearchAuthenticRAG.py  # Search only"
