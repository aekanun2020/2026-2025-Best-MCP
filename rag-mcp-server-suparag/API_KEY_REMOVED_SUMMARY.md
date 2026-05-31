# Alibaba API Key Removed

**Date**: 2026-04-15  
**Status**: ✅ Successfully removed and disabled

---

## Changes Made

### 1. `.env` file
**Before:**
```bash
DASHSCOPE_API_KEY=sk-REDACTED_SET_VIA_ENV
```

**After:**
```bash
# DASHSCOPE_API_KEY=sk-REDACTED_SET_VIA_ENV
```

✅ Commented out (disabled)

---

### 2. `.env.example` file
**Before:**
```bash
# API Keys
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

**After:**
```bash
# API Keys (Optional - only needed for generate_answer tool)
# DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

✅ Commented out with note that it's optional

---

## Impact

### What Still Works ✅
- **search_documentation** - Hybrid search (BM25 + Vector + RRF)
- **add_documents** - Index documents (but context generation will fail)
- **OpenSearch** - All search functionality
- **BGE-M3 Embeddings** - Via Ollama (no API key needed)

### What Doesn't Work ❌
- **generate_answer** - Already disabled (commented out)
- **Context Generation** - `add_documents` will fail when trying to generate contextualized content
  - Uses `call_qwen_api()` which requires `DASHSCOPE_API_KEY`

---

## Warning from Docker Compose

```
WARN[0000] The "DASHSCOPE_API_KEY" variable is not set. Defaulting to a blank string.
```

This is **expected** and **safe** because:
- The API key is now commented out in `.env`
- The `generate_answer` tool is disabled
- The system doesn't need Qwen API anymore

---

## Container Status

```bash
docker ps --filter "name=contextual-rag-mcp"
```

**Output:**
```
NAMES                STATUS
contextual-rag-mcp   Up 31 seconds (healthy)
```

✅ Container is running and healthy

---

## Verification

### Test search (should work)
```bash
curl -s http://localhost:9001/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"search_documentation",
      "arguments":{"query":"โรค","limit":3}
    }
  }' | jq -r '.result.content[0].text'
```

**Expected:** Returns search results (no API key needed)

---

### Test add_documents (will partially fail)
```bash
curl -s http://localhost:9001/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"add_documents",
      "arguments":{"path":"/app/rag/corpus_input"}
    }
  }' | jq -r '.result.content[0].text'
```

**Expected:** Will fail at context generation step because:
```python
# In authenticRAG.py
def generate_context(self, document_content, chunk_content):
    context = self.call_qwen_api(prompt, max_tokens=100, temperature=0.1)
    # ↑ This will fail: DASHSCOPE_API_KEY not set
```

---

## Why Remove API Key?

### 1. Cost Savings 💰
- Qwen 2.5-32B API costs money per request
- No longer needed since `generate_answer` is disabled

### 2. Security 🔒
- API keys should not be stored in plain text
- Commented out = not loaded into environment

### 3. Simplification 🎯
- System now only uses local resources:
  - OpenSearch (local)
  - Ollama BGE-M3 (local)
  - No external API dependencies

---

## Current System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ MCP Server (Port 9001)                                  │
│                                                          │
│ Tools:                                                   │
│  ✅ search_documentation (Hybrid Search)                │
│  ⚠️  add_documents (Context generation will fail)       │
│  ❌ generate_answer (Disabled)                          │
└─────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│ OpenSearch       │          │ Ollama           │
│ (Port 9201)      │          │ (Port 11435)     │
│                  │          │                  │
│ - BM25 Index     │          │ - BGE-M3         │
│ - Vector Index   │          │   (Embeddings)   │
│ - 53 chunks      │          │                  │
└──────────────────┘          └──────────────────┘

❌ Alibaba Cloud (Qwen API) - REMOVED
```

---

## How to Re-enable API Key

### 1. Uncomment in `.env`
```bash
DASHSCOPE_API_KEY=sk-REDACTED_SET_VIA_ENV
```

### 2. Restart container
```bash
docker-compose restart mcp-server
```

### 3. Re-enable generate_answer tool
Uncomment the code in `main.py` (see `TOOL_DISABLED_SUMMARY.md`)

### 4. Rebuild container
```bash
docker-compose rm -sf mcp-server
docker-compose build mcp-server
docker-compose up -d mcp-server
```

---

## Files Modified

1. ✅ `2026-ContextualRAG-MCP-Streamable-HTTP/.env`
   - Commented out `DASHSCOPE_API_KEY`

2. ✅ `2026-ContextualRAG-MCP-Streamable-HTTP/.env.example`
   - Commented out `DASHSCOPE_API_KEY`
   - Added note: "Optional - only needed for generate_answer tool"

3. ✅ Container restarted
   - MCP server running without API key
   - Status: Healthy

---

## Summary

**Before:**
- 3 tools (search, add, generate)
- Qwen API key active
- External API dependency

**After:**
- 2 tools (search, add*)
- Qwen API key disabled
- Local-only system
- *add_documents will fail at context generation

**Recommendation:**
If you need to index new documents with context generation, you'll need to:
1. Re-enable the API key temporarily
2. Run `add_documents`
3. Disable the API key again

Or modify `add_documents` to skip context generation when API key is not available.
