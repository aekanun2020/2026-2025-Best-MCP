#!/bin/bash

# Start all containers (if not running)
echo "=== Starting All Containers ==="
echo "This will start containers that are not running"
echo "Existing data will be preserved"
echo ""

# Start all services
docker-compose up -d

# Wait a bit
sleep 3

# Show status
echo ""
echo "=== Container Status ==="
docker-compose ps

echo ""
echo "=== Checking Services ==="
echo "Qdrant: http://localhost:6333"
echo "Ollama: http://localhost:11434"
echo "PyRAGDoc: http://localhost:8000"
echo ""
echo "To view logs: docker-compose logs -f [service_name]"
echo "Services: qdrant, ollama, pyragdoc"
