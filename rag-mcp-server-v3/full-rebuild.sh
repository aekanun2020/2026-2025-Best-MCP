#!/bin/bash

# Full rebuild script - removes all containers and rebuilds everything
echo "=== Full Rebuild Script ==="
echo "⚠️  WARNING: This will remove ALL containers and rebuild from scratch"
echo "⚠️  All data will be lost unless you have backups"
echo ""

# Ask for confirmation
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo "Starting full rebuild..."

# Stop all containers
echo "1. Stopping all containers..."
docker compose down

# Remove containers (but keep volumes for now)
echo "2. Removing containers..."
docker compose rm -f

# Remove images to force rebuild
echo "3. Removing old images..."
docker rmi v2-2026-mcp-sse-rag-fixed-pyragdoc:latest 2>/dev/null || true

# Set permissions
echo "4. Setting permissions..."
chmod +x ollama-entrypoint.sh
chmod +x *.sh

# Build all services with no cache
echo "5. Building all services (this may take a while)..."
docker compose build --no-cache

# Start all services
echo "6. Starting all services..."
docker compose up -d

# Wait for services to start
echo "7. Waiting for services to initialize..."
sleep 30

# Check status
echo "8. Checking service status..."
./check-status.sh

echo ""
echo "=== Full rebuild completed! ==="
echo ""
echo "Services should be available at:"
echo "  - Qdrant: http://localhost:6333"
echo "  - Ollama: http://localhost:11434"
echo "  - PyRAGDoc: http://localhost:8000"
echo ""
echo "To test the new add_context tool:"
echo "  ./test-add-context.sh"
echo ""
echo "To run full test suite:"
echo "  ./test-mcp-tools-curl.sh"
echo ""
echo "To view logs:"
echo "  docker compose logs -f pyragdoc"