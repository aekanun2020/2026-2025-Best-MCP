# Curl Testing Guide - MCP Tools

## Overview
คู่มือนี้อธิบายวิธีทดสอบ MCP server tools โดยตรงด้วย curl (ไม่ต้องผ่าน web UI)

## Prerequisites

1. **Server ต้องรันอยู่:**
   ```bash
   docker-compose ps
   # ต้องเห็น pyragdoc container running
   ```

2. **ตรวจสอบ health:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Dependencies:**
   - `curl` - HTTP client
   - `jq` - JSON processor (optional, สำหรับ pretty print)

## Test Scripts

### 1. Full Test Suite (ทดสอบทุก tool + ทุก parameter)
```bash
./test-mcp-tools-curl.sh
```

**ทดสอบอะไรบ้าง:**
- ✅ Health check
- ✅ MCP initialize
- ✅ List tools
- ✅ List sources
- ✅ Search with default mode (hybrid)
- ✅ Search with semantic mode
- ✅ Search with BM25 mode
- ✅ Search with hybrid mode (explicit)
- ✅ Search with Thai numerals
- ✅ Search with mixed queries
- ✅ Invalid mode error handling
- ✅ Different limit values

**Output:** JSON responses จาก MCP server พร้อม color coding

---

### 2. Search Mode Comparison (เปรียบเทียบ 3 โหมด)
```bash
./compare-search-modes.sh
```

**ทดสอบอะไรบ้าง:**
- 6 queries ที่ครอบคลุมทุกกรณี
- แสดงผลลัพธ์จาก semantic, BM25, และ hybrid แบบ side-by-side
- เหมาะสำหรับดูความแตกต่างระหว่างโหมด

**Test Queries:**
1. `ข้อ ๘๖` - Thai section number (BM25 should excel)
2. `๒๑` - Thai numeral only (BM25 should excel)
3. `ข้อ ๒๑` - Section number (BM25 should excel)
4. `ก.พ.ว.` - Thai abbreviation (BM25 should excel)
5. `การแต่งตั้งตำแหน่งทางวิชาการ` - Conceptual (Semantic should excel)
6. `ข้อ ๘๖ การแต่งตั้ง` - Mixed (Hybrid should excel)

---

## Manual Testing

### Basic Search (Default = Hybrid)
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2024-11-05" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "ข้อ ๒๑",
        "limit": 5
      }
    }
  }' | jq '.'
```

### Search with Specific Mode
```bash
# Semantic mode
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "การแต่งตั้ง",
        "limit": 3,
        "search_mode": "semantic"
      }
    }
  }' | jq '.'

# BM25 mode
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "ข้อ ๘๖",
        "limit": 3,
        "search_mode": "bm25"
      }
    }
  }' | jq '.'

# Hybrid mode (explicit)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "ก.พ.ว.",
        "limit": 3,
        "search_mode": "hybrid"
      }
    }
  }' | jq '.'
```

### List Sources
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_sources",
      "arguments": {}
    }
  }' | jq '.'
```

### List Available Tools
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }' | jq '.'
```

---

## Understanding the Response

### Success Response
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[1] formatted_regulations (Score: 0.95)\nSource: /home/mcpuser/documents/formatted_regulations.md\n\n### ข้อ ๒๑\n..."
      }
    ]
  }
}
```

### Error Response
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "Invalid search_mode: must be 'semantic', 'bm25', or 'hybrid'"
  }
}
```

---

## Interpreting Results

### Score Interpretation
- **0.8 - 1.0**: Excellent match (highly relevant)
- **0.6 - 0.8**: Good match (relevant)
- **0.4 - 0.6**: Fair match (somewhat relevant)
- **< 0.4**: Poor match (may not be relevant)

### Mode-Specific Behavior

**Semantic Mode:**
- Scores based on embedding similarity (cosine distance)
- Good for conceptual/meaning-based queries
- May miss exact matches (e.g., "ข้อ ๒๑")

**BM25 Mode:**
- Scores based on term frequency and document frequency
- Excellent for exact matching
- May miss conceptual matches

**Hybrid Mode (Default):**
- Combines both using Reciprocal Rank Fusion (RRF)
- RRF formula: score = Σ(1/(k + rank_i)) where k=60
- Best of both worlds
- Documents appearing in both result sets get higher scores

---

## Troubleshooting

### Server Not Responding
```bash
# Check if container is running
docker-compose ps

# Check server logs
docker-compose logs -f pyragdoc

# Restart if needed
./rebuild-safe.sh
```

### BM25 Index Not Built
Check logs for:
```
INFO - Building BM25 index from Qdrant documents...
INFO - Loaded X documents from Qdrant
INFO - ✅ BM25 index built successfully with X documents
```

If missing:
```bash
# Restart server to rebuild index
docker-compose restart pyragdoc

# Check logs again
docker-compose logs -f pyragdoc
```

### Invalid Mode Error
```json
{
  "error": {
    "message": "Invalid search_mode: must be 'semantic', 'bm25', or 'hybrid'"
  }
}
```

**Solution:** Use only these values: `"semantic"`, `"bm25"`, or `"hybrid"`

### No Results Found
```
"No results found for your query."
```

**Possible causes:**
1. No documents in Qdrant
2. Query doesn't match any documents
3. BM25 index not built (for BM25/hybrid modes)

**Check:**
```bash
# Check Qdrant documents
./check-qdrant.sh

# Or use Python script
python check-qdrant.py
```

---

## Performance Testing

### Measure Response Time
```bash
time curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "ข้อ ๒๑",
        "limit": 5,
        "search_mode": "hybrid"
      }
    }
  }' | jq '.'
```

### Expected Performance
- **Semantic only**: ~100-300ms
- **BM25 only**: ~10-50ms
- **Hybrid**: ~150-400ms (slightly slower due to RRF)

---

## Next Steps

1. ✅ Run `./test-mcp-tools-curl.sh` to verify all tools work
2. ✅ Run `./compare-search-modes.sh` to see mode differences
3. ✅ Test with your own queries
4. ✅ Integrate with web UI client

---

## Related Files

- `test-mcp-tools-curl.sh` - Full test suite
- `compare-search-modes.sh` - Mode comparison
- `WEB_UI_TESTING_GUIDE.md` - Web UI integration guide
- `HYBRID_SEARCH_CONFIG.md` - Performance tuning guide
- `check-qdrant.sh` - Qdrant status checker

---

## Support

If you encounter issues:
1. Check server logs: `docker-compose logs -f pyragdoc`
2. Check Qdrant: `./check-qdrant.sh`
3. Verify BM25 index was built (see logs)
4. Try restarting: `./rebuild-safe.sh`
