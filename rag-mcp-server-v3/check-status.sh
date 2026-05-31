#!/bin/bash

# Check status of all containers and services
echo "=== Docker Container Status ==="
docker-compose ps

echo ""
echo "=== Service Health Checks ==="

# Check Qdrant
echo -n "Qdrant (port 6333): "
if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Check Ollama
echo -n "Ollama (port 11434): "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Check PyRAGDoc
echo -n "PyRAGDoc (port 8000): "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo ""
echo "=== Recent Logs (last 20 lines) ==="
echo "--- PyRAGDoc ---"
docker-compose logs --tail=20 pyragdoc

echo ""
echo "To view full logs: docker-compose logs -f [service_name]"
