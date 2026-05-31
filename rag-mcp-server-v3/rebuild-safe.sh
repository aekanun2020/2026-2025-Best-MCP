#!/bin/bash

# Safe rebuild script - DOES NOT remove volumes or stop other services
echo "=== Safe Rebuild PyRAGDoc Container ==="
echo "This script will rebuild ONLY the pyragdoc container"
echo "Qdrant and Ollama data will be preserved"
echo ""

# Make sure ollama-entrypoint.sh has execute permission
echo "Setting permissions..."
chmod +x ollama-entrypoint.sh

# Stop only pyragdoc container (keep qdrant and ollama running)
echo "Stopping pyragdoc container..."
docker-compose stop pyragdoc

# Remove only pyragdoc container (not volumes!)
echo "Removing old pyragdoc container..."
docker-compose rm -f pyragdoc

# Build pyragdoc with no cache
echo "Building pyragdoc container with hybrid search..."
docker-compose build --no-cache pyragdoc

# Start pyragdoc container
echo "Starting pyragdoc container..."
docker-compose up -d pyragdoc

# Show logs
echo ""
echo "=== Container started! Showing logs... ==="
echo "Press Ctrl+C to stop viewing logs (container will keep running)"
echo ""
sleep 2
docker-compose logs -f pyragdoc
