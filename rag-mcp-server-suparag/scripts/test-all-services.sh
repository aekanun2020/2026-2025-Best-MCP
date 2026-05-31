#!/bin/bash
# Test all services with NEW ports

echo "Testing all services..."
echo "======================"

# Test OpenSearch (9201)
echo -e "\n1. OpenSearch (9201):"
curl -s http://localhost:9201/_cluster/health | jq .

# Test Ollama (11435)
echo -e "\n2. Ollama (11435):"
curl -s http://localhost:11435/api/tags | jq .

# Test MCP Server (9001)
echo -e "\n3. MCP Server (9001):"
curl -s http://localhost:9001/health | jq .

# Test Streamlit (9501)
echo -e "\n4. Streamlit (9501):"
curl -s -I http://localhost:9501 | head -n 1

echo -e "\n✅ All services tested!"
