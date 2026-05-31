#!/bin/bash

# Quick script to check Qdrant collections using curl
echo "=== Checking Qdrant Collections ==="
echo ""

# Check if Qdrant is running
echo "Checking Qdrant connection..."
if ! curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    echo "❌ Qdrant is not responding on port 6333"
    echo ""
    echo "Check if container is running:"
    echo "  docker-compose ps qdrant"
    exit 1
fi

echo "✅ Qdrant is running"
echo ""

# Get collections
echo "=== Collections ==="
curl -s http://localhost:6333/collections | jq '.result.collections[] | {name: .name, points_count: .points_count}'

echo ""
echo "=== Detailed Collection Info ==="

# Get collection names
COLLECTIONS=$(curl -s http://localhost:6333/collections | jq -r '.result.collections[].name')

for collection in $COLLECTIONS; do
    echo ""
    echo "📦 Collection: $collection"
    echo "---"
    curl -s "http://localhost:6333/collections/$collection" | jq '{
        points_count: .result.points_count,
        vectors_count: .result.vectors_count,
        indexed_vectors_count: .result.indexed_vectors_count,
        status: .result.status
    }'
done

echo ""
echo "=== For more details, run: ==="
echo "  python3 check-qdrant.py"
