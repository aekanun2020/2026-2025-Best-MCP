#!/bin/bash
# Test MCP Server on port 9001

echo "Testing MCP Server on port 9001..."
echo "=================================="

# Test health endpoint
echo -e "\n1. Health Check:"
curl -s http://localhost:9001/health | jq .

# Test MCP initialize
echo -e "\n2. MCP Initialize:"
curl -s -X POST http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }' | jq .

# Test tools/list
echo -e "\n3. MCP Tools List:"
curl -s -X POST http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }' | jq .

# Test search_documentation
echo -e "\n4. Search Documentation:"
curl -s -X POST http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "test query",
        "limit": 3
      }
    }
  }' | jq .

echo -e "\n✅ MCP Server tests complete!"
