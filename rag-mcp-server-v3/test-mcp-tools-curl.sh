#!/bin/bash

# MCP Server Tool Testing Script
# Tests all MCP tools with various parameters using curl

set -e

# Configuration
MCP_HOST="${MCP_HOST:-localhost}"
MCP_PORT="${MCP_PORT:-8000}"
BASE_URL="http://${MCP_HOST}:${MCP_PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to make MCP JSON-RPC call
mcp_call() {
    local method=$1
    local params=$2
    local id=${3:-1}
    
    local payload=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "id": $id,
    "method": "$method",
    "params": $params
}
EOF
)
    
    echo "$payload" | jq '.' 2>/dev/null || echo "$payload"
    echo ""
    
    curl -s -X POST "$BASE_URL/mcp" \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2024-11-05" \
        -d "$payload" | jq '.' 2>/dev/null || echo "Failed to parse response"
}

# Test 1: Health Check
print_header "TEST 1: Health Check"
print_info "Testing server health endpoint..."
curl -s "$BASE_URL/health" | jq '.'
print_success "Health check completed"

# Test 2: Initialize
print_header "TEST 2: Initialize MCP Session"
print_info "Initializing MCP session..."
mcp_call "initialize" '{"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}'
print_success "Initialize completed"

# Test 3: List Tools
print_header "TEST 3: List Available Tools"
print_info "Listing all available tools..."
mcp_call "tools/list" '{}'
print_success "Tools list completed"

# Test 4: List Sources
print_header "TEST 4: List Documentation Sources"
print_info "Calling list_sources tool..."
mcp_call "tools/call" '{"name": "list_sources", "arguments": {}}'
print_success "List sources completed"

# Test 5: Search - Default (Hybrid Mode)
print_header "TEST 5: Search Documentation - Default (Hybrid)"
print_info "Query: 'ข้อ ๒๑' (should use hybrid mode by default)"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "ข้อ ๒๑",
        "limit": 3
    }
}' 5
print_success "Hybrid search (default) completed"

# Test 6: Search - Semantic Mode
print_header "TEST 6: Search Documentation - Semantic Mode"
print_info "Query: 'การแต่งตั้งตำแหน่งทางวิชาการ' (semantic mode)"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "การแต่งตั้งตำแหน่งทางวิชาการ",
        "limit": 3,
        "search_mode": "semantic"
    }
}' 6
print_success "Semantic search completed"

# Test 7: Search - BM25 Mode
print_header "TEST 7: Search Documentation - BM25 Mode"
print_info "Query: 'ข้อ ๘๖' (BM25 mode - exact matching)"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "ข้อ ๘๖",
        "limit": 3,
        "search_mode": "bm25"
    }
}' 7
print_success "BM25 search completed"

# Test 8: Search - Hybrid Mode (Explicit)
print_header "TEST 8: Search Documentation - Hybrid Mode (Explicit)"
print_info "Query: 'ก.พ.ว.' (hybrid mode - abbreviation)"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "ก.พ.ว.",
        "limit": 3,
        "search_mode": "hybrid"
    }
}' 8
print_success "Hybrid search (explicit) completed"

# Test 9: Search - Thai Numeral Only
print_header "TEST 9: Search Documentation - Thai Numeral"
print_info "Query: '๒๑' (Thai numeral only)"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "๒๑",
        "limit": 3,
        "search_mode": "hybrid"
    }
}' 9
print_success "Thai numeral search completed"

# Test 10: Search - Mixed Query
print_header "TEST 10: Search Documentation - Mixed Query"
print_info "Query: 'ข้อ ๘๖ การแต่งตั้ง' (exact term + concept)"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "ข้อ ๘๖ การแต่งตั้ง",
        "limit": 5,
        "search_mode": "hybrid"
    }
}' 10
print_success "Mixed query search completed"

# Test 11: Search - Invalid Mode (Error Test)
print_header "TEST 11: Search Documentation - Invalid Mode"
print_info "Query: 'test' with invalid search_mode (should fail gracefully)"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "test",
        "limit": 3,
        "search_mode": "invalid_mode"
    }
}' 11
print_info "Invalid mode test completed (should show error)"

# Test 12: Add Context Tool
print_header "TEST 12: Add Context Tool"
print_info "Testing add_context tool with sample conversation data..."
mcp_call "tools/call" '{
    "name": "add_context",
    "arguments": {
        "content": "ผู้ใช้ถามเกี่ยวกับการติดตั้ง Docker บน Ubuntu และได้รับคำแนะนำให้ใช้คำสั่ง apt-get update && apt-get install docker.io จากนั้นเริ่มต้น service ด้วย systemctl start docker",
        "title": "Docker Installation Guide - Ubuntu",
        "source": "chat_conversation",
        "metadata": {
            "conversation_id": "test_conv_001",
            "user_os": "ubuntu",
            "issue_type": "installation"
        }
    }
}' 12
print_success "Add context completed"

# Test 13: Search for Added Context
print_header "TEST 13: Search for Added Context"
print_info "Searching for the context we just added..."
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "Docker installation Ubuntu",
        "limit": 3,
        "search_mode": "hybrid"
    }
}' 13
print_success "Context search completed"

# Test 14: Search - Different Limits
print_header "TEST 14: Search Documentation - Different Limits"
print_info "Testing with limit=1, 5, 10"

echo -e "\n${YELLOW}Limit = 1:${NC}"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "ข้อ ๒๑",
        "limit": 1,
        "search_mode": "hybrid"
    }
}' 14

echo -e "\n${YELLOW}Limit = 10:${NC}"
mcp_call "tools/call" '{
    "name": "search_documentation",
    "arguments": {
        "query": "ข้อ ๒๑",
        "limit": 10,
        "search_mode": "hybrid"
    }
}' 15

print_success "Limit tests completed"

# Summary
print_header "TEST SUMMARY"
print_success "All curl tests completed!"
print_info "Check the output above for any errors or unexpected results"
print_info ""
print_info "Key observations to check:"
print_info "  1. Hybrid mode (default) should combine BM25 + semantic results"
print_info "  2. BM25 mode should excel at exact matching (ข้อ ๘๖, ๒๑, ก.พ.ว.)"
print_info "  3. Semantic mode should excel at conceptual queries"
print_info "  4. add_context tool should successfully store conversation data"
print_info "  5. Added context should be searchable immediately"
print_info "  6. Invalid mode should return error message"
print_info "  7. All modes should respect the limit parameter"
print_info ""
print_info "Server logs: docker-compose logs -f pyragdoc"
