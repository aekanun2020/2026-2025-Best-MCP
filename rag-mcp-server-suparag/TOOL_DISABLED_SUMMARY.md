# Tool Disabled: generate_answer

**Date**: 2026-04-15  
**Status**: ✅ Successfully disabled

---

## Changes Made

### File: `mcp-server/main.py`

#### 1. Tool Definition (Commented Out)
```python
# In tools/list response
# {
#     "name": "generate_answer",
#     "description": "Generate answer using RAG pipeline",
#     "inputSchema": {
#         "type": "object",
#         "properties": {
#             "query": {"type": "string", "description": "Question to answer"},
#             "use_context": {"type": "boolean", "default": True, "description": "Use search context"}
#         },
#         "required": ["query"]
#     }
# }
```

#### 2. Tool Execution (Commented Out)
```python
# In tools/call handler
# elif name == "generate_answer":
#     result = await generate_answer(**arguments)
```

#### 3. Function Implementation (Commented Out)
```python
# async def generate_answer(query: str, use_context: bool = True) -> str:
#     """Generate answer using RAG pipeline"""
#     try:
#         if not rag_client:
#             return "Error: RAG client not initialized"
#         
#         logger.info(f"Generating answer for: '{query}' (use_context={use_context})")
#         
#         if use_context:
#             # Use search_for_question which does hybrid search + answer generation
#             answer = rag_client.search_for_question(query, k=5)
#         else:
#             # Direct answer without context using call_qwen_api
#             answer = rag_client.call_qwen_api(query)
#         
#         return answer
#     
#     except Exception as e:
#         logger.error(f"Error generating answer: {e}", exc_info=True)
#         return f"Error generating answer: {str(e)}"
```

---

## Available Tools (After Change)

### ✅ Active Tools
1. **search_documentation** - Search with Contextual Retrieval (Hybrid: BM25 + Vector + RRF)
2. **add_documents** - Index documents with context generation (Qwen API)

### ❌ Disabled Tools
1. **generate_answer** - Generate answer using RAG pipeline (COMMENTED OUT)

---

## Verification

### Command
```bash
curl -s http://localhost:9001/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | jq '.result.tools[] | .name'
```

### Output
```
"search_documentation"
"add_documents"
```

✅ Confirmed: `generate_answer` is no longer listed

---

## Why Disabled?

The `generate_answer` tool uses **Qwen 2.5-32B API** which:
- Costs money per API call
- Requires `DASHSCOPE_API_KEY`
- Adds latency (LLM inference time)

By disabling it, the system:
- ✅ Saves API costs
- ✅ Faster responses (search only)
- ✅ Still provides full document retrieval via `search_documentation`

---

## Impact

### What Still Works
- ✅ Hybrid search (BM25 + Vector + RRF)
- ✅ Document indexing with context generation
- ✅ Contextual retrieval
- ✅ All OpenSearch functionality
- ✅ BGE-M3 embeddings via Ollama

### What Doesn't Work
- ❌ Automatic answer generation from search results
- ❌ RAG pipeline (search + LLM generation)
- ❌ Direct LLM queries without context

### Workaround
Users can:
1. Use `search_documentation` to get relevant documents
2. Read the documents themselves
3. Or use external LLM with the retrieved context

---

## How to Re-enable

### 1. Uncomment the code in `main.py`
```python
# Remove the # comments from:
# - Tool definition in tools/list
# - Tool execution in tools/call
# - Function implementation
```

### 2. Rebuild container
```bash
cd 2026-ContextualRAG-MCP-Streamable-HTTP
docker-compose rm -sf mcp-server
docker-compose build mcp-server
docker-compose up -d mcp-server
```

### 3. Verify
```bash
curl -s http://localhost:9001/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | jq '.result.tools[] | .name'
```

Should show:
```
"search_documentation"
"add_documents"
"generate_answer"  ← Back!
```

---

## Container Status

```bash
docker ps --filter "name=contextual-rag"
```

| Container | Status | Port |
|-----------|--------|------|
| contextual-rag-mcp | ✅ Running | 9001 |
| contextual-rag-opensearch | ✅ Running | 9201 |
| contextual-rag-ollama | ✅ Running | 11435 |
| contextual-rag-ui | ✅ Running | 9501 |

---

## Summary

**Before:**
- 3 tools: search_documentation, add_documents, generate_answer

**After:**
- 2 tools: search_documentation, add_documents
- generate_answer is commented out (not deleted, can be re-enabled)

**Reason:**
- Avoid Qwen API costs
- Faster responses
- Search-only functionality is sufficient for most use cases
