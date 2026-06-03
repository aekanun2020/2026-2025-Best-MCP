# RAG MCP Server with Streamable HTTP Transport

MCP server สำหรับค้นหาเอกสาร (RAG) แบบ **Hybrid Search** (BM25 + Semantic + RRF) รองรับภาษาไทย ผ่าน **Streamable HTTP transport** (มาตรฐาน MCP ปัจจุบัน ใช้ endpoint เดียว แทน HTTP+SSE แบบเก่า) รันเป็น container ด้วย Docker

ใช้ **Qdrant** เป็น vector database และ **Ollama** (หรือ OpenAI) สำหรับสร้าง embedding — ทั้งสองตัวรันแยกอยู่นอก container ตัวนี้

## Features

- **Streamable HTTP Transport** — ใช้ endpoint เดียว (`/mcp`) รับ POST/GET/DELETE ตามมาตรฐาน MCP ปัจจุบัน
- **Stateless** — ไม่บังคับ `Mcp-Session-Id` (คล้าย FastMCP `stateless_http=True`) ต่อ client ได้หลากหลาย
- **Hybrid Search** — รวม BM25 (keyword) + Semantic (vector) เข้าด้วยกันด้วย RRF (Reciprocal Rank Fusion)
- **Thai Language Support** — ตัดคำ/normalize ภาษาไทย (รองรับเลขไทย ๑๒๓) ด้วย PyThaiNLP
- **FastAPI + Uvicorn backend** — web framework ที่เร็วและทันสมัย
- **Docker Support** — รันเป็น container ได้ทั้งหมด

### MCP Tools (4)

| Tool | หน้าที่ |
|------|--------|
| `search_documentation` | ค้นหาเอกสารที่เก็บไว้ (รับ `query`, `limit` default 5) — ใช้ Hybrid Search เป็นค่าเริ่มต้น |
| `list_sources` | ลิสต์ source ของเอกสารทั้งหมดที่เก็บอยู่ |
| `add_directory` | เพิ่มไฟล์เอกสารทั้งโฟลเดอร์เข้าระบบ (รับ `path`) |
| `add_context` | เพิ่ม text content ตรงๆ เข้า RAG store เช่น context จาก agent (รับ `content`, `title`, `source`, `metadata`) |

## Installation

> **Prerequisites:**
> 1. ติดตั้งและเปิด **Docker Desktop** ก่อน ([Mac](https://docs.docker.com/desktop/install/mac-install/) / [Windows](https://docs.docker.com/desktop/install/windows-install/))
> 2. มี **Qdrant** รันอยู่ที่ port **6333** และ **Ollama** รันอยู่ที่ port **11434** บนเครื่อง host (รันแยกไว้ก่อน) และ pull embedding model ไว้: `ollama pull nomic-embed-text`
> 3. port **9000** บนเครื่องว่าง

ขั้นตอน Windows กับ Mac ต่างกันเล็กน้อย ทำตามหัวข้อของ OS ตัวเอง

---

### Windows (double-click)

**1. ดาวน์โหลดโปรเจกต์จาก GitHub**

เปิด `Command Prompt` (CMD) แล้วรัน:

```cmd
git clone https://github.com/aekanun2020/2026-2025-Best-MCP.git
cd 2026-2025-Best-MCP\rag-mcp-server-streamablehttp
```

(ไม่มี Git? กดปุ่มสีเขียว **Code ▾** ที่ [หน้า repo](https://github.com/aekanun2020/2026-2025-Best-MCP) → **Download ZIP** → แตกไฟล์ → เปิดโฟลเดอร์ `rag-mcp-server-streamablehttp`)

**2. เริ่มรัน server**

เปิดโฟลเดอร์ `rag-mcp-server-streamablehttp` ใน File Explorer แล้ว **double-click ไฟล์ `start_docker.bat`**

หน้าต่าง CMD จะเปิดขึ้นมาและทำให้ทั้งหมดให้อัตโนมัติ:
- สร้าง `.env` จาก `.env.example` (ถ้ายังไม่มี)
- build Docker image
- รัน container และแสดง log สด

**3. เสร็จ**

เมื่อเห็น log ขึ้น health แล้ว server จะรันที่ **http://localhost:9000/mcp**
เปิดหน้าต่าง CMD ค้างไว้ — **ปิดหน้าต่าง = server หยุด** ถ้าจะหยุดให้ปิดหน้าต่างหรือกด `Ctrl + C`

---

### Mac (Terminal)

**1. ดาวน์โหลดโปรเจกต์จาก GitHub**

เปิด `Terminal` แล้วรัน:

```bash
git clone https://github.com/aekanun2020/2026-2025-Best-MCP.git
cd 2026-2025-Best-MCP/rag-mcp-server-streamablehttp
```

**2. เริ่มรัน server**

```bash
chmod +x start_docker.sh   # ทำแค่ครั้งแรกครั้งเดียว
./start_docker.sh
```

script จะสร้าง `.env` จาก `.env.example` (ถ้ายังไม่มี), build image, รัน container และแสดง log สด

**3. เสร็จ**

เมื่อเห็น log ขึ้น health แล้ว server จะรันที่ **http://localhost:9000/mcp**
เปิด Terminal ค้างไว้ — ปิดหน้าต่าง (หรือกด `Ctrl + C`) = server หยุด

---

### Configuration

ตัวติดตั้งจะ copy [`.env.example`](.env.example) ไปเป็น `.env` ให้อัตโนมัติ โดยตั้งค่าไว้สำหรับ Qdrant + Ollama ที่รันบน**เครื่องเดียวกัน**กับ Docker Desktop:

```env
QDRANT_URL=http://host.docker.internal:6333
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_URL=http://host.docker.internal:11434
OPENAI_API_KEY=
```

`host.docker.internal` ช่วยให้ container เข้าถึง Qdrant/Ollama บนเครื่อง host ได้ ถ้า Qdrant/Ollama อยู่ที่อื่น ให้แก้ `.env` (แล้วรัน start script ใหม่) เปลี่ยน `QDRANT_URL` / `OLLAMA_URL` ให้ตรง

ถ้าจะใช้ OpenAI แทน Ollama ให้ตั้ง `EMBEDDING_PROVIDER=openai` และใส่ `OPENAI_API_KEY`

## Managing the container

ชื่อ container คือ **`rag-mcp-streamable-http`** — รันคำสั่งเหล่านี้จากในโฟลเดอร์ `rag-mcp-server-streamablehttp`

```bash
# เช็คสถานะ / health
docker ps

# ดู log สด
docker logs -f rag-mcp-streamable-http

# หยุด server (เก็บ container ไว้ start ใหม่ได้)
docker compose stop

# เปิดใช้งานใหม่ภายหลัง
docker compose start
```

## Re-running with a new configuration

ถ้าแก้ `.env` (เช่น เปลี่ยน `QDRANT_URL` หรือ `EMBEDDING_MODEL`) ให้ apply config ใหม่ด้วยการ **rebuild + recreate** container ในที่เดิม:

```bash
docker compose up -d --build --force-recreate
```

> **ห้ามรัน `docker compose down`** — `down` จะลบ container พร้อม network (และอาจกระทบ resource อื่น) ซึ่งไม่จำเป็น
> คำสั่ง `up -d --build --force-recreate` จะ recreate container ในที่พร้อม `.env`/config ใหม่ให้อยู่แล้ว — ใช้แค่คำสั่งนี้คำสั่งเดียว

## API Endpoints

`/mcp` เป็น endpoint เดียวของ Streamable HTTP รองรับ 3 method:

| Method / Path | หน้าที่ |
|---------------|--------|
| `POST /mcp` | รับ JSON-RPC message ของ MCP (ตัวหลักที่ใช้สื่อสาร) |
| `GET /mcp` | เปิด SSE stream — ต้องส่ง `Accept: text/event-stream` ไม่งั้นคืน **405** ตาม spec |
| `DELETE /mcp` | ปิด session — คืน **204** ถ้ามี session, **404** ถ้าไม่มี |
| `GET /health` | Health check (ใช้โดย Docker healthcheck) |
| `GET /` | ข้อมูล service และรายการ endpoint |

### Session handling (stateless)

Server ทำงานแบบ **stateless** (คล้าย FastMCP `stateless_http=True`):
ตอน `initialize` จะ mint `Mcp-Session-Id` ส่งกลับมาใน response header ไว้ให้ client ที่ต้องการใช้ (optional)
แต่ request ถัดไป (`tools/list`, `tools/call`) จะคืน JSON response ตรงๆ **โดยไม่บังคับ** header นี้
ทำให้ client ที่ไม่ได้ส่ง session id กลับมา (เช่น Streamable HTTP path ของ PyClaw) ต่อได้โดยไม่ต้องแก้อะไร

> **Note:** บน Docker server รันภายในที่ port **8000** แต่ expose ออกมาภายนอกที่ port **9000**

## MCP Client Configuration

สำหรับ Claude Desktop หรือ MCP client อื่นๆ ให้ต่อผ่าน `mcp-remote` (มันทำหน้าที่ bridge จาก Streamable HTTP server ไปเป็น stdio ที่ client เหล่านี้ต้องการ):

```json
{
  "mcpServers": {
    "rag-streamable-http": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:9000/mcp",
        "--allow-http"
      ]
    }
  }
}
```

ถ้า client อยู่คนละเครื่องกับ server ให้เปลี่ยน `localhost` เป็น IP ของ server (เช่น LAN หรือ Tailscale address) ส่วน `--allow-http` จำเป็นเพราะ server เสิร์ฟผ่าน HTTP ธรรมดา ไม่ใช่ HTTPS

## License

MIT
