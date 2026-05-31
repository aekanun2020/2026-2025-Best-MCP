#!/bin/bash

# Quick test script for hybrid search
echo "=== Quick Hybrid Search Test ==="
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ PyRAGDoc server is not running"
    echo ""
    echo "Start the server first:"
    echo "  ./start-all.sh"
    echo "  or"
    echo "  ./rebuild-safe.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Make script executable
chmod +x test-hybrid-search.py

# Run the test
echo "Running comprehensive hybrid search tests..."
echo ""
python3 test-hybrid-search.py
