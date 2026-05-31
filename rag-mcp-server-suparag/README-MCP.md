# Contextual RAG MCP Server

MCP Server with Contextual Retrieval, Hybrid Search, and Streamable HTTP transport.

## Features

- ✅ **MCP Protocol** - Full MCP 2024-11-05 support
- ✅ **Contextual Retrieval** - Qwen API context generation
- ✅ **Hybrid Search** - BM25 + Vector + RRF
- ✅ **Dual Indexing** - OpenSearch (vector + BM25)
- ✅ **SSE Streaming** - Real-time responses
- ✅ **Containerized** - 4 Docker containers
- ✅ **Web UI** - Streamlit interface

## Architecture

```
4 Containers:
1. contextual-rag-mcp (Port 9001) - MCP Server
2. contextual-rag-opensearch (Port 9201) - Dual-index storage
3. contextual-rag-ollama (Port 11435) - Qwen API + embeddings
4. contextual-rag-ui (Port 9501) - Streamlit UI
```

## Quick Start

### 1. Setup Environment

```bash
cd 2026-ContextualRAG-MCP-Streamable-HTTP

# Copy .env file
cp .env.example .env

# Edit .env and add your DASHSCOPE_API_KEY
nano .env
```

### 2. Start All Services

```bash
# Start containers
./scripts/start-all.sh

# Or manually
docker-compose up -d --build
```

### 3. Check Health

```bash
./scripts/check-health.sh
```

### 4. Test MCP Server

```bash
./scripts/test-mcp-server.sh
```

## Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **MCP Server** | http://localhost:9001/mcp | MCP protocol endpoint |
| **OpenSearch** | http://localhost:9201 | Search engine API |
| **Ollama** | http://localhost:11435 | Qwen API |
| **Streamlit** | http://localhost:9501 | Web UI |

## MCP Tools

### 1. search_documentation

Search with Contextual Retrieval (Hybrid: BM25 + Vector + RRF)

```bash
curl -X POST http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "โรคหัดเยอรมัน",
        "limit": 5
      }
    }
  }'
```

### 2. add_documents

Index documents with context generation (Qwen API)

```bash
curl -X POST http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "add_documents",
      "arguments": {
        "path": "/app/rag/corpus_input"
      }
    }
  }'
```

### 3. generate_answer

Generate answer using RAG pipeline

```bash
curl -X POST http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "generate_answer",
      "arguments": {
        "query": "อาการของโรคหัดเยอรมัน",
        "use_context": true
      }
    }
  }'
```

## MCP Client Configuration

### Kiro

```json
{
  "mcpServers": {
    "contextual-rag": {
      "url": "http://localhost:9001/mcp",
      "transport": "http"
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "contextual-rag": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "contextual-rag-mcp",
        "python",
        "-m",
        "main"
      ]
    }
  }
}
```

## Management Commands

```bash
# Start all containers
docker-compose up -d

# Stop all containers
docker-compose stop

# Restart specific container
docker-compose restart mcp-server

# View logs
docker-compose logs -f mcp-server

# Remove all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v
```

## Testing Scripts

```bash
# Test all services
./scripts/test-all-services.sh

# Test MCP server only
./scripts/test-mcp-server.sh

# Check health
./scripts/check-health.sh
```

## Troubleshooting

### Port Conflicts

If ports are already in use:

```bash
# Check what's using ports
lsof -i :9001 :9201 :11435 :9501

# Stop conflicting containers
docker stop <container_name>
```

### Container Issues

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

### OpenSearch Issues

```bash
# Check OpenSearch health
curl http://localhost:9201/_cluster/health

# Check indices
curl http://localhost:9201/_cat/indices
```

### Ollama Issues

```bash
# Check Ollama models
curl http://localhost:11435/api/tags

# Pull models manually
docker exec -it contextual-rag-ollama ollama pull qwen2.5:14b
```

## Development

### Project Structure

```
2026-ContextualRAG-MCP-Streamable-HTTP/
├── mcp-server/                  # MCP Server (NEW)
│   ├── main.py                  # FastAPI + MCP
│   ├── mcp_tools.py             # Tool wrappers
│   ├── Dockerfile
│   └── requirements.txt
│
├── AuthenticRAG-Qwen2.5API/     # Existing RAG (UNCHANGED)
│   ├── authenticRAG.py          # Core RAG logic
│   ├── streamlit_app.py         # Web UI
│   └── Dockerfile
│
├── scripts/                     # Testing scripts
│   ├── start-all.sh
│   ├── test-mcp-server.sh
│   ├── test-all-services.sh
│   └── check-health.sh
│
├── docker-compose.yml           # 4 containers
├── ollama-entrypoint.sh         # Ollama setup
└── .env.example                 # Environment template
```

### Tech Stack

**Same baseline as v4 project:**
- FastAPI 0.115+
- MCP 1.2+
- Uvicorn 0.32+
- OpenSearch 2.17.1
- Ollama (Qwen 2.5:14b)
- Sentence Transformers 3.2+

## License

MIT
