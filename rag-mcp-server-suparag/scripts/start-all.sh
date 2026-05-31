#!/bin/bash
# Start all containers

echo "Starting Contextual RAG MCP Server..."
echo "======================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env and add your DASHSCOPE_API_KEY"
    exit 1
fi

# Start containers
echo "Starting containers..."
docker-compose up -d --build

# Wait for services
echo "Waiting for services to start..."
sleep 30

# Check health
echo -e "\nChecking service health..."
./scripts/check-health.sh

echo -e "\n✅ All services started!"
echo -e "\nAccess URLs:"
echo "  MCP Server:  http://localhost:9001/mcp"
echo "  OpenSearch:  http://localhost:9201"
echo "  Ollama:      http://localhost:11435"
echo "  Streamlit:   http://localhost:9501"
