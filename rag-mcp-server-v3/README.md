# PyRAGDoc MCP Server v3 - Hybrid Search + Dynamic Context

MCP Server สำหรับ RAG documentation system รองรับ Hybrid Search ที่รวม BM25 (keyword matching) และ Semantic Search (dense vectors) ด้วย Reciprocal Rank Fusion (RRF) พร้อมฟีเจอร์ใหม่ **Dynamic Context Addition**

## Local Repository Path

```
/Users/grizzlymacbookpro/Desktop/test/2026-02-01/2025-from-web-to-agenticrag/v2-2026-mcp-sse-rag-fixed
```

## Remote Repository

```
https://github.com/aekanun2020/v3-2026-mcp-streamable-sse-rag.git
```

## Version 3 Features

**🆕 NEW in v3:**
- **Dynamic Context Addition**: Agent สามารถเก็บ context จากการสนทนาลง vector database ได้โดยตรง
- **add_context Tool**: เพิ่ม tool ใหม่สำหรับเก็บ Q&A, troubleshooting steps, และข้อมูลจาก external sources
- **Metadata Support**: รองรับการเก็บ metadata และ source tracking
- **Immediate Searchability**: Context ที่เพิ่มใหม่สามารถค้นหาได้ทันที

**Core Features:**
- **Hybrid Search**: รวม BM25 + Semantic + RRF สำหรับผลลัพธ์ที่ดีที่สุด
- **Thai Language Support**: รองรับการค้นหาภาษาไทย รวมถึงเลขไทย (๑, ๒, ๓...)
- **Multiple Transport**: Streamable HTTP และ SSE
- **Vector Database**: Qdrant
- **Embedding**: Ollama (default) หรือ OpenAI

## Quick Start v3

### 1. Clone and Start Services

```bash
git clone https://github.com/aekanun2020/v3-2026-mcp-streamable-sse-rag.git
cd v3-2026-mcp-streamable-sse-rag
cp .env.example .env
./full-rebuild.sh  # หรือ docker compose up --build -d
```

Services:
- PyRAGDoc Server: `http://localhost:8000`
- Qdrant: `http://localhost:6333`
- Ollama: `http://localhost:11434`

### 2. Add Documents (Traditional Way)

```bash
# Set permission (ถ้าจำเป็น)
docker exec -u root pyrag-sse-server chmod -R 777 /home/mcpuser/documents

# Copy documents เข้า container
docker cp your-document.md pyrag-sse-server:/home/mcpuser/documents/

# Index documents
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add_directory",
      "arguments": {"path": "/home/mcpuser/documents"}
    }
  }'
```

### 2b. 🆕 Add Context Dynamically (NEW in v3)

```bash
# เพิ่ม context จากการสนทนาหรือข้อมูลภายนอก
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add_context",
      "arguments": {
        "content": "ผู้ใช้ถามเกี่ยวกับการติดตั้ง Docker และได้รับคำแนะนำให้ใช้คำสั่ง apt-get install docker.io",
        "title": "Docker Installation Guide",
        "source": "chat_conversation",
        "metadata": {"user_os": "ubuntu", "issue_type": "installation"}
      }
    }
  }'
```

### 3. Search

```bash
# Hybrid search (default - แนะนำ)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "ข้อ ๗",
        "limit": 5,
        "search_mode": "hybrid"
      }
    }
  }'
```

## Search Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `hybrid` | BM25 + Semantic + RRF (default) | ทุกกรณี - แนะนำ |
| `bm25` | Keyword matching | exact terms, เลขข้อ, ตัวย่อ |
| `semantic` | Dense vector similarity | conceptual queries |

### ตัวอย่างการใช้งาน

```bash
# BM25 - ค้นหาเลขข้อแบบ exact match
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {"query": "ข้อ ๘๖", "search_mode": "bm25"}
    }
  }'

# Semantic - ค้นหาแนวคิด
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {"query": "การแต่งตั้งตำแหน่งทางวิชาการ", "search_mode": "semantic"}
    }
  }'

# เพิ่ม context จาก agent
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add_context",
      "arguments": {
        "content": "ผู้ใช้ถามเกี่ยวกับขั้นตอนการสมัครงาน และได้รับคำตอบว่าต้องส่งเอกสาร 3 ชิ้น คือ ใบสมัคร, ประวัติ, และใบรับรอง",
        "title": "Q&A: ขั้นตอนการสมัครงาน",
        "source": "chat_conversation",
        "metadata": {"conversation_id": "conv_123", "timestamp": "2026-02-01"}
      }
    }
  }'
```

## MCP Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `search_documentation` | `query` (required), `limit` (default: 5), `search_mode` (default: hybrid) | ค้นหาเอกสาร |
| `list_sources` | - | แสดงรายการเอกสารที่ index แล้ว |
| `add_directory` | `path` (required) | เพิ่มเอกสารจาก directory |
| `add_context` | `content` (required), `title` (optional), `source` (default: agent_context), `metadata` (optional) | เพิ่ม context โดยตรงเข้า database |

## MCP Client Configuration

### Claude Desktop / Kiro

```json
{
  "mcpServers": {
    "pyragdoc": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

### Langflow (Docker Container)

เมื่อใช้ Langflow ที่รันบน Docker container ให้ใช้ URL:

```
http://host.docker.internal:8000/mcp
```

**หมายเหตุ**: `host.docker.internal` เป็น special DNS name ที่ Docker ใช้สำหรับเชื่อมต่อจาก container ไปยัง host machine

## 🧪 Testing v3 Features

### Test All Tools (รวม add_context ใหม่)
```bash
./test-mcp-tools-curl.sh
```

### Test add_context Tool เฉพาะ
```bash
./test-add-context.sh
```

### Compare Search Modes
```bash
./compare-search-modes.sh
```

### Check System Status
```bash
./check-status.sh
```

## 🔧 Management Scripts v3

### Full Rebuild (ใหม่)
```bash
./full-rebuild.sh  # Rebuild ทั้งหมดจากศูนย์
```

### Safe Rebuild (เฉพาะ PyRAGDoc)
```bash
./rebuild-safe.sh  # เก็บข้อมูล Qdrant และ Ollama
```

### Container Management
```bash
./start-all.sh           # Start all containers
./cleanup-containers.sh  # Clean up old containers
./check-status.sh        # Check service status
```

## 🎯 Use Cases for add_context Tool

1. **Q&A Knowledge Base**: เก็บคำถาม-คำตอบจากการสนทนา
2. **Troubleshooting Database**: บันทึกการแก้ปัญหาและขั้นตอน
3. **External Data Integration**: เก็บข้อมูลจาก APIs หรือแหล่งภายนอก
4. **Dynamic Documentation**: สร้างเอกสารแบบ real-time จากการใช้งาน

**ตัวอย่าง Use Cases:**
```bash
# เก็บการแก้ปัญหา
add_context(
  content="ผู้ใช้รายงาน SSL error แก้ไขโดยการ update certificate",
  title="SSL Certificate Fix",
  source="technical_support"
)

# เก็บข้อมูลจาก API
add_context(
  content="ข้อมูลราคาล่าสุดจาก API: BTC $45,000",
  title="Crypto Price Update",
  source="external_api"
)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp` | POST | MCP JSON-RPC messages |
| `/mcp` | GET | SSE stream (optional) |
| `/health` | GET | Health check |
| `/` | GET | Server info |

## Configuration (.env)

```env
QDRANT_URL=http://localhost:6333
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_URL=http://localhost:11434
```

## Supported File Types

`.pdf`, `.txt`, `.md`, `.markdown`, `.py`, `.js`, `.java`, `.c`, `.cpp`, `.html`, `.css`, `.json`, `.yaml`, `.yml`, `.xml`

## Troubleshooting v3

### BM25 Index Empty
ตรวจสอบ log:
```bash
docker logs pyrag-sse-server | grep BM25
```
ถ้าเห็น "No documents to index in BM25" ต้อง add_directory หรือ add_context ก่อน

### add_context Tool Issues
```bash
# ตรวจสอบว่า tool มีอยู่
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# ทดสอบ add_context
./test-add-context.sh
```

### Permission Denied
```bash
docker exec -u root pyrag-sse-server chmod -R 777 /home/mcpuser/documents
```

### Check Services
```bash
./check-status.sh  # ตรวจสอบทุก service พร้อมกัน

# หรือตรวจสอบแยก
curl http://localhost:6333/collections  # Qdrant
curl http://localhost:11434/api/tags    # Ollama
curl http://localhost:8000/health       # PyRAGDoc
```

### Container Issues
```bash
# ดู logs
docker compose logs -f pyragdoc

# Restart services
./rebuild-safe.sh

# Full rebuild (ลบทุกอย่าง)
./full-rebuild.sh
```

## What's New in v3

- ✅ **add_context Tool**: เพิ่ม context แบบ dynamic
- ✅ **Metadata Support**: รองรับ metadata และ source tracking  
- ✅ **Immediate Search**: Context ใหม่ค้นหาได้ทันที
- ✅ **Enhanced Testing**: Scripts ทดสอบครบถ้วน
- ✅ **Better Management**: Scripts จัดการ container ที่ดีขึ้น
- ✅ **Comprehensive Docs**: เอกสารและคู่มือสมบูรณ์

## Migration from v2

1. Clone v3 repository
2. Copy your `.env` file
3. Run `./full-rebuild.sh`
4. Test new features with `./test-add-context.sh`

## License

MIT
