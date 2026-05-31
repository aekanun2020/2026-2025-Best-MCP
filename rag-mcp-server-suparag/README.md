# 🚀 SupaRAG

> **Superior RAG with Contextual Retrieval & MCP Integration**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-2025--11--25-orange.svg)](https://modelcontextprotocol.io/)

Production-ready Retrieval-Augmented Generation system featuring **Anthropic's Contextual Retrieval**, **Hybrid Search** (BM25 + Vector + RRF), and **Model Context Protocol** integration.

---

## ✨ Features

- 🧠 **Contextual Retrieval** - Anthropic's approach for enhanced accuracy
- 🔍 **Hybrid Search** - BM25 + Vector Search + Reciprocal Rank Fusion
- 🔌 **MCP Integration** - Model Context Protocol (Streamable HTTP)
- 🌐 **Dual Indexing** - OpenSearch with vector + BM25 indices
- 🤖 **Qwen API** - Context generation with Qwen 2.5-32B-Instruct
- 📊 **BGE-M3 Embeddings** - 1024-dimensional vectors via Ollama
- 🐳 **Fully Dockerized** - 4 containers, ready to deploy
- 🎨 **Web UI** - Streamlit interface with document management
- 🇹🇭 **Thai Language Support** - Full support for Thai and English

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SupaRAG System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ MCP Server   │  │  Streamlit   │  │  OpenSearch  │     │
│  │  (Port 9001) │  │  (Port 9501) │  │  (Port 9201) │     │
│  │              │  │              │  │              │     │
│  │ • FastAPI    │  │ • Web UI     │  │ • Vector     │     │
│  │ • MCP Tools  │  │ • Doc Mgmt   │  │ • BM25       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                   ┌────────▼────────┐                       │
│                   │     Ollama      │                       │
│                   │  (Port 11435)   │                       │
│                   │                 │                       │
│                   │ • BGE-M3        │                       │
│                   │ • Qwen 2.5:14b  │                       │
│                   └─────────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM
- 20GB+ disk space

### 1. Clone Repository

```bash
git clone https://github.com/aekanun2020/SupaRAG.git
cd SupaRAG
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Qwen API key (optional for context generation)
```

### 3. Start All Services

```bash
docker-compose up -d
```

### 4. Access Services

- **MCP Server**: http://localhost:9001
- **Streamlit UI**: http://localhost:9501
- **OpenSearch**: http://localhost:9201
- **Ollama**: http://localhost:11435

---

## 📖 Usage

### Via MCP Tools (Kiro/Claude Desktop)

Configure in `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "suparag": {
      "command": "docker",
      "args": ["exec", "-i", "contextual-rag-mcp", "python", "-m", "mcp"],
      "disabled": false,
      "autoApprove": ["search_documentation", "add_documents"]
    }
  }
}
```

**Available Tools:**
- `search_documentation` - Hybrid search with contextual retrieval
- `add_documents` - Index documents with context generation

### Via Web UI

1. Open http://localhost:9501
2. **Search Tab**: Ask questions and get answers
3. **Document Management Tab**: Upload, edit, delete documents

### Via Python API

```python
from authenticRAG import AnthropicStyleContextualRAG

# Initialize
rag = AnthropicStyleContextualRAG(
    opensearch_host="localhost",
    opensearch_port=9201,
    ollama_base_url="http://localhost:11435"
)

# Search
results = rag.hybrid_search("What is the bearing temperature standard?", top_k=5)

# Add documents
rag.add_documents_with_context("/path/to/documents")
```

---

## 🔧 Configuration

### Environment Variables

```bash
# OpenSearch
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200

# Ollama
OLLAMA_BASE_URL=http://ollama:11434

# Qwen API (optional - for context generation)
DASHSCOPE_API_KEY=your-api-key-here

# MCP Server
MCP_HOST=0.0.0.0
MCP_PORT=8001
```

### Docker Compose Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| MCP Server | 8001 | 9001 |
| Streamlit UI | 8501 | 9501 |
| OpenSearch | 9200 | 9201 |
| Ollama | 11434 | 11435 |

---

## 📊 How It Works

### 1. Document Indexing with Context

```
Document → Chunk → Generate Context (Qwen API) → Embed (BGE-M3) → Store
                                                                      ↓
                                                    OpenSearch (Vector + BM25)
```

### 2. Hybrid Search with RRF

```
Query → Embed (BGE-M3) → Vector Search (OpenSearch)
                      ↘                              ↘
                        BM25 Search (OpenSearch) → RRF Fusion → Top Results
```

### 3. Contextual Retrieval

Each chunk is enhanced with document-level context:

```
Original Chunk:
"Bearing temperature should not exceed 80°C."

With Context:
"This document discusses centrifugal pump maintenance standards. 
Bearing temperature should not exceed 80°C."
```

---

## 🎯 Key Technologies

- **[Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)** - Enhanced RAG accuracy
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** - Standardized AI integration
- **[OpenSearch](https://opensearch.org/)** - Dual-index search engine
- **[Ollama](https://ollama.ai/)** - Local LLM and embeddings
- **[BGE-M3](https://huggingface.co/BAAI/bge-m3)** - Multilingual embeddings
- **[Qwen 2.5](https://qwenlm.github.io/)** - Context generation
- **[FastAPI](https://fastapi.tiangolo.com/)** - MCP server
- **[Streamlit](https://streamlit.io/)** - Web interface

---

## 📁 Project Structure

```
SupaRAG/
├── mcp-server/              # MCP Server (FastAPI)
│   ├── main.py             # MCP endpoints
│   ├── mcp_tools.py        # Tool implementations
│   ├── Dockerfile
│   └── requirements.txt
├── AuthenticRAG-Qwen2.5API/ # Core RAG Engine
│   ├── authenticRAG.py     # Main RAG logic
│   ├── streamlit_app.py    # Web UI
│   ├── api_server.py       # REST API
│   ├── corpus_input/       # Document storage
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml       # All services
├── .env.example            # Environment template
└── README.md               # This file
```

---

## 🧪 Testing

### Test MCP Server

```bash
curl http://localhost:9001/health
```

### Test Search

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
        "query": "bearing temperature",
        "limit": 5
      }
    }
  }'
```

### Test Document Indexing

```bash
curl -X POST http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add_documents",
      "arguments": {
        "path": "/app/rag/corpus_input"
      }
    }
  }'
```

---

## 📚 Documentation

- **[User Guide](README-USER.md)** - For end users
- **[Developer Guide](README-DEV.md)** - For developers
- **[MCP Integration](README-MCP.md)** - MCP setup and usage
- **[Document Management](STREAMLIT_DOCUMENT_MANAGEMENT.md)** - UI guide

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) - For Contextual Retrieval approach
- [Model Context Protocol](https://modelcontextprotocol.io/) - For MCP specification
- [OpenSearch](https://opensearch.org/) - For search engine
- [Ollama](https://ollama.ai/) - For local LLM hosting
- [BAAI](https://huggingface.co/BAAI) - For BGE-M3 embeddings
- [Alibaba Cloud](https://www.alibabacloud.com/) - For Qwen API

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/aekanun2020/SupaRAG/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aekanun2020/SupaRAG/discussions)

---

<div align="center">

**SupaRAG** - Superior RAG with Contextual Retrieval & MCP Integration

Made with ❤️ by [aekanun2020](https://github.com/aekanun2020)

⭐ Star us on GitHub if you find this useful!

</div>
