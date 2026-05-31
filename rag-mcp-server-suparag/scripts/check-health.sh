#!/bin/bash
# Check health of all services

echo "Checking service health..."
echo "=========================="

# Function to check service
check_service() {
    local name=$1
    local url=$2
    
    echo -n "Checking $name... "
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Check all services
check_service "OpenSearch" "http://localhost:9201/_cluster/health"
check_service "Ollama" "http://localhost:11435/api/tags"
check_service "MCP Server" "http://localhost:9001/health"
check_service "Streamlit" "http://localhost:9501"

echo -e "\nDone!"
