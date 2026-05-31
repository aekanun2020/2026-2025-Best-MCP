# Volume Mapping Guide - Complete Reference

**Project Path:** `/Users/grizzlymacbookpro/Desktop/test/2026-04-15/2026-ContextualRAG-MCP-Streamable-HTTP`

---

## 📦 Container 1: MCP Server

### Container Name
```
contextual-rag-mcp
```

### Volume Mappings
```yaml
volumes:
  - ./AuthenticRAG-Qwen2.5API:/app/rag:ro
```

### Detailed Mapping

| Host (Mac) | Container | Mode | Purpose |
|------------|-----------|------|---------|
| `./AuthenticRAG-Qwen2.5API` | `/app/rag` | Read-Only | Mount authenticRAG.py code |

### Full Paths

**Host:**
```
/Users/grizzlymacbookpro/Desktop/test/2026-04-15/2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API
```

**Container:**
```
/app/rag
```

### What's Inside?
```
/app/rag/
├── authenticRAG.py          ← Main RAG code
├── corpus_input/            ← Document directory
│   ├── sample-1.md
│   └── sample-2.md
├── streamlit_app.py
├── requirements.txt
└── ...
```

### Access from Container
```bash
# Read authenticRAG.py
docker exec contextual-rag-mcp cat /app/rag/authenticRAG.py

# List corpus files
docker exec contextual-rag-mcp ls -la /app/rag/corpus_input/

# Cannot write (read-only)
docker exec contextual-rag-mcp touch /app/rag/test.txt
# Error: Read-only file system
```

---

## 📦 Container 2: OpenSearch

### Container Name
```
contextual-rag-opensearch
```

### Volume Mappings
```yaml
volumes:
  - opensearch-data:/usr/share/opensearch/data
```

### Detailed Mapping

| Host (Docker Volume) | Container | Mode | Purpose |
|---------------------|-----------|------|---------|
| `opensearch-data` | `/usr/share/opensearch/data` | Read-Write | Persistent data storage |

### Volume Type
**Named Volume** (managed by Docker)

### Full Paths

**Host (Docker Volume):**
```
/var/lib/docker/volumes/2026-contextualrag-mcp-streamable-http_opensearch-data/_data
```

**Container:**
```
/usr/share/opensearch/data
```

### What's Inside?
```
/usr/share/opensearch/data/
├── nodes/
│   └── 0/
│       ├── indices/
│       │   ├── anthropic-vector-index/
│       │   └── anthropic-bm25-index/
│       └── _state/
└── ...
```

### Access from Container
```bash
# List data directory
docker exec contextual-rag-opensearch ls -la /usr/share/opensearch/data/

# Check disk usage
docker exec contextual-rag-opensearch du -sh /usr/share/opensearch/data/
```

### Inspect Volume
```bash
# List all volumes
docker volume ls | grep opensearch

# Inspect volume
docker volume inspect 2026-contextualrag-mcp-streamable-http_opensearch-data

# Backup volume
docker run --rm -v 2026-contextualrag-mcp-streamable-http_opensearch-data:/data -v $(pwd):/backup alpine tar czf /backup/opensearch-backup.tar.gz /data
```

---

## 📦 Container 3: Ollama

### Container Name
```
contextual-rag-ollama
```

### Volume Mappings
```yaml
volumes:
  - ollama-data:/root/.ollama
  - ./ollama-entrypoint.sh:/entrypoint.sh:ro
```

### Detailed Mapping

| Host | Container | Mode | Purpose |
|------|-----------|------|---------|
| `ollama-data` (named volume) | `/root/.ollama` | Read-Write | Model storage |
| `./ollama-entrypoint.sh` | `/entrypoint.sh` | Read-Only | Startup script |

### Full Paths

**Host (Docker Volume):**
```
/var/lib/docker/volumes/2026-contextualrag-mcp-streamable-http_ollama-data/_data
```

**Host (File):**
```
/Users/grizzlymacbookpro/Desktop/test/2026-04-15/2026-ContextualRAG-MCP-Streamable-HTTP/ollama-entrypoint.sh
```

**Container:**
```
/root/.ollama          ← Models stored here
/entrypoint.sh         ← Startup script
```

### What's Inside?
```
/root/.ollama/
├── models/
│   ├── manifests/
│   │   └── registry.ollama.ai/
│   │       └── library/
│   │           ├── bge-m3/
│   │           ├── qwen2.5/
│   │           └── nomic-embed-text/
│   └── blobs/
│       └── sha256-xxxxx...
└── ...
```

### Access from Container
```bash
# List models
docker exec contextual-rag-ollama ollama list

# Check model storage
docker exec contextual-rag-ollama du -sh /root/.ollama/

# View entrypoint script
docker exec contextual-rag-ollama cat /entrypoint.sh
```

---

## 📦 Container 4: Streamlit UI

### Container Name
```
contextual-rag-ui
```

### Volume Mappings
```yaml
volumes:
  - ./AuthenticRAG-Qwen2.5API:/app
  - ./AuthenticRAG-Qwen2.5API/corpus_input:/app/corpus_input
```

### Detailed Mapping

| Host (Mac) | Container | Mode | Purpose |
|------------|-----------|------|---------|
| `./AuthenticRAG-Qwen2.5API` | `/app` | Read-Write | Full app directory |
| `./AuthenticRAG-Qwen2.5API/corpus_input` | `/app/corpus_input` | Read-Write | Document storage |

### Full Paths

**Host:**
```
/Users/grizzlymacbookpro/Desktop/test/2026-04-15/2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API
/Users/grizzlymacbookpro/Desktop/test/2026-04-15/2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API/corpus_input
```

**Container:**
```
/app
/app/corpus_input
```

### What's Inside?
```
/app/
├── streamlit_app.py         ← Streamlit UI code
├── authenticRAG.py
├── requirements.txt
├── corpus_input/            ← Document directory (read-write)
│   ├── sample-1.md
│   └── sample-2.md
└── ...
```

### Access from Container
```bash
# List app directory
docker exec contextual-rag-ui ls -la /app/

# List corpus files
docker exec contextual-rag-ui ls -la /app/corpus_input/

# Read a file
docker exec contextual-rag-ui cat /app/corpus_input/sample-1.md

# Create a file (read-write)
docker exec contextual-rag-ui sh -c 'echo "# Test" > /app/corpus_input/test.md'

# Verify on host
cat AuthenticRAG-Qwen2.5API/corpus_input/test.md
```

### Why Two Mappings?

**First Mapping:**
```yaml
- ./AuthenticRAG-Qwen2.5API:/app
```
Maps the entire directory to `/app`

**Second Mapping:**
```yaml
- ./AuthenticRAG-Qwen2.5API/corpus_input:/app/corpus_input
```
Explicitly maps corpus_input (redundant but ensures clarity)

**Note:** The second mapping is technically redundant since it's already included in the first mapping, but it makes the intent clear.

---

## 🗂️ Complete Directory Structure

### Host Machine (Mac)
```
/Users/grizzlymacbookpro/Desktop/test/2026-04-15/2026-ContextualRAG-MCP-Streamable-HTTP/
├── AuthenticRAG-Qwen2.5API/              ← Mapped to containers
│   ├── authenticRAG.py
│   ├── streamlit_app.py
│   ├── corpus_input/                     ← Document storage
│   │   ├── sample-1.md
│   │   └── sample-2.md
│   ├── requirements.txt
│   └── ...
├── mcp-server/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── ollama-entrypoint.sh                  ← Mapped to ollama container
├── docker-compose.yml
└── .env
```

### Container: contextual-rag-mcp
```
/app/
├── main.py                               ← From mcp-server/
├── rag/                                  ← Mapped from AuthenticRAG-Qwen2.5API/
│   ├── authenticRAG.py
│   ├── corpus_input/
│   │   ├── sample-1.md
│   │   └── sample-2.md
│   └── ...
└── ...
```

### Container: contextual-rag-ui
```
/app/                                     ← Mapped from AuthenticRAG-Qwen2.5API/
├── streamlit_app.py
├── authenticRAG.py
├── corpus_input/                         ← Document storage (read-write)
│   ├── sample-1.md
│   └── sample-2.md
└── ...
```

### Container: contextual-rag-opensearch
```
/usr/share/opensearch/
├── data/                                 ← Named volume: opensearch-data
│   └── nodes/
│       └── 0/
│           └── indices/
│               ├── anthropic-vector-index/
│               └── anthropic-bm25-index/
└── ...
```

### Container: contextual-rag-ollama
```
/root/.ollama/                            ← Named volume: ollama-data
├── models/
│   ├── manifests/
│   └── blobs/
└── ...
/entrypoint.sh                            ← Mapped from ollama-entrypoint.sh
```

---

## 🔄 Data Flow

### Adding a Document via Streamlit UI

```
1. User uploads file in browser
   ↓
2. Streamlit saves to /app/corpus_input/new-doc.md (in container)
   ↓
3. Docker volume mapping syncs to host
   ↓
4. File appears on host: ./AuthenticRAG-Qwen2.5API/corpus_input/new-doc.md
   ↓
5. MCP Server can read from /app/rag/corpus_input/new-doc.md (read-only)
   ↓
6. Index to OpenSearch → stored in opensearch-data volume
```

### Searching a Document

```
1. User searches via Streamlit UI
   ↓
2. Streamlit calls MCP Server API (http://mcp-server:8001)
   ↓
3. MCP Server queries OpenSearch (http://opensearch:9200)
   ↓
4. OpenSearch reads from /usr/share/opensearch/data/ (opensearch-data volume)
   ↓
5. Results returned to Streamlit
   ↓
6. Displayed in browser
```

---

## 📊 Volume Types Comparison

### Bind Mounts (Host → Container)
**Used by:**
- MCP Server: `./AuthenticRAG-Qwen2.5API:/app/rag`
- Streamlit: `./AuthenticRAG-Qwen2.5API:/app`
- Ollama: `./ollama-entrypoint.sh:/entrypoint.sh`

**Characteristics:**
- ✅ Direct access to host files
- ✅ Changes sync immediately
- ✅ Easy to edit on host
- ⚠️ Path must exist on host
- ⚠️ Permissions can be tricky

### Named Volumes (Docker-managed)
**Used by:**
- OpenSearch: `opensearch-data:/usr/share/opensearch/data`
- Ollama: `ollama-data:/root/.ollama`

**Characteristics:**
- ✅ Managed by Docker
- ✅ Persistent across container restarts
- ✅ Better performance
- ⚠️ Not directly accessible on host
- ⚠️ Need docker commands to access

---

## 🔧 Useful Commands

### Check Volume Mappings
```bash
# Inspect container volumes
docker inspect contextual-rag-ui | jq '.[0].Mounts'
docker inspect contextual-rag-mcp | jq '.[0].Mounts'

# List all volumes
docker volume ls

# Inspect specific volume
docker volume inspect 2026-contextualrag-mcp-streamable-http_opensearch-data
```

### Test File Sync
```bash
# Create file on host
echo "# Test from host" > AuthenticRAG-Qwen2.5API/corpus_input/test-host.md

# Check in Streamlit container
docker exec contextual-rag-ui cat /app/corpus_input/test-host.md

# Check in MCP container
docker exec contextual-rag-mcp cat /app/rag/corpus_input/test-host.md

# Create file in container
docker exec contextual-rag-ui sh -c 'echo "# Test from container" > /app/corpus_input/test-container.md'

# Check on host
cat AuthenticRAG-Qwen2.5API/corpus_input/test-container.md
```

### Backup Volumes
```bash
# Backup OpenSearch data
docker run --rm \
  -v 2026-contextualrag-mcp-streamable-http_opensearch-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/opensearch-backup.tar.gz /data

# Backup Ollama models
docker run --rm \
  -v 2026-contextualrag-mcp-streamable-http_ollama-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/ollama-backup.tar.gz /data
```

### Restore Volumes
```bash
# Restore OpenSearch data
docker run --rm \
  -v 2026-contextualrag-mcp-streamable-http_opensearch-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/opensearch-backup.tar.gz --strip 1"
```

---

## 📝 Summary Table

| Container | Host Path | Container Path | Mode | Type |
|-----------|-----------|----------------|------|------|
| **MCP Server** | `./AuthenticRAG-Qwen2.5API` | `/app/rag` | RO | Bind Mount |
| **Streamlit** | `./AuthenticRAG-Qwen2.5API` | `/app` | RW | Bind Mount |
| **Streamlit** | `./AuthenticRAG-Qwen2.5API/corpus_input` | `/app/corpus_input` | RW | Bind Mount |
| **OpenSearch** | `opensearch-data` (volume) | `/usr/share/opensearch/data` | RW | Named Volume |
| **Ollama** | `ollama-data` (volume) | `/root/.ollama` | RW | Named Volume |
| **Ollama** | `./ollama-entrypoint.sh` | `/entrypoint.sh` | RO | Bind Mount |

**Legend:**
- RO = Read-Only
- RW = Read-Write

---

## 🎯 Key Takeaways

1. **Streamlit UI** has **read-write** access to `corpus_input/`
   - Can add, edit, delete files
   - Changes sync to host immediately

2. **MCP Server** has **read-only** access to `corpus_input/`
   - Can read files for indexing
   - Cannot modify files

3. **OpenSearch & Ollama** use **named volumes**
   - Data persists across container restarts
   - Not directly accessible on host filesystem

4. **Bind mounts** sync **bidirectionally**
   - Changes on host → visible in container
   - Changes in container → visible on host

5. **corpus_input/** is the **shared space**
   - Streamlit writes documents here
   - MCP Server reads documents from here
   - Both containers see the same files
