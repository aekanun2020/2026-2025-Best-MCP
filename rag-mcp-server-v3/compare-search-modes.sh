#!/bin/bash

# Compare Search Modes Script
# Side-by-side comparison of semantic, BM25, and hybrid search

set -e

# Configuration
MCP_HOST="${MCP_HOST:-localhost}"
MCP_PORT="${MCP_PORT:-8000}"
BASE_URL="http://${MCP_HOST}:${MCP_PORT}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_mode() {
    local mode=$1
    case $mode in
        "semantic")
            echo -e "${CYAN}🔍 SEMANTIC SEARCH (Dense Vector)${NC}"
            ;;
        "bm25")
            echo -e "${GREEN}📝 BM25 SEARCH (Sparse Keyword)${NC}"
            ;;
        "hybrid")
            echo -e "${MAGENTA}🔀 HYBRID SEARCH (RRF Combined)${NC}"
            ;;
    esac
}

# Function to search with specific mode
search_with_mode() {
    local query=$1
    local mode=$2
    local limit=${3:-3}
    
    local payload=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search_documentation",
        "arguments": {
            "query": "$query",
            "limit": $limit,
            "search_mode": "$mode"
        }
    }
}
EOF
)
    
    curl -s -X POST "$BASE_URL/mcp" \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2024-11-05" \
        -d "$payload" | jq -r '.result.content[0].text // .error.message // "No response"'
}

# Function to compare all modes for a query
compare_query() {
    local query=$1
    local description=$2
    local limit=${3:-3}
    
    print_header "QUERY: $query"
    echo -e "${YELLOW}Description: $description${NC}\n"
    
    # Semantic
    print_mode "semantic"
    search_with_mode "$query" "semantic" $limit
    echo ""
    
    # BM25
    print_mode "bm25"
    search_with_mode "$query" "bm25" $limit
    echo ""
    
    # Hybrid
    print_mode "hybrid"
    search_with_mode "$query" "hybrid" $limit
    echo ""
    
    echo -e "${YELLOW}───────────────────────────────────────────────────────────${NC}\n"
}

# Main comparison tests
print_header "🧪 SEARCH MODE COMPARISON TEST"
echo -e "${YELLOW}Comparing Semantic vs BM25 vs Hybrid search modes${NC}\n"

# Test 1: Thai section number with numeral
compare_query "ข้อ ๘๖" \
    "Thai section number with Thai numeral (BM25 should excel)" \
    3

# Test 2: Thai numeral only
compare_query "๒๑" \
    "Thai numeral only (BM25 should excel)" \
    3

# Test 3: Section number
compare_query "ข้อ ๒๑" \
    "Section number (BM25 should excel)" \
    3

# Test 4: Thai abbreviation
compare_query "ก.พ.ว." \
    "Thai abbreviation (BM25 should excel)" \
    3

# Test 5: Conceptual query
compare_query "การแต่งตั้งตำแหน่งทางวิชาการ" \
    "Conceptual query (Semantic should excel)" \
    3

# Test 6: Mixed query
compare_query "ข้อ ๘๖ การแต่งตั้ง" \
    "Mixed: exact term + concept (Hybrid should excel)" \
    5

# Summary
print_header "📊 SUMMARY"
echo -e "${GREEN}✓ Comparison completed!${NC}\n"
echo -e "${YELLOW}Expected Results:${NC}"
echo -e "  ${CYAN}Semantic:${NC} Good for conceptual/meaning-based queries"
echo -e "  ${GREEN}BM25:${NC} Good for exact matching (numbers, abbreviations)"
echo -e "  ${MAGENTA}Hybrid:${NC} Best of both worlds (default mode)"
echo -e ""
echo -e "${YELLOW}Key Improvements with Hybrid Search:${NC}"
echo -e "  ✓ Thai section numbers (ข้อ ๘๖, ข้อ ๒๑) now work"
echo -e "  ✓ Thai numerals (๒๑) now work"
echo -e "  ✓ Thai abbreviations (ก.พ.ว.) now work"
echo -e "  ✓ Conceptual queries still work well"
echo -e "  ✓ Mixed queries get best results"
echo -e ""
echo -e "${BLUE}View server logs:${NC} docker-compose logs -f pyragdoc"
