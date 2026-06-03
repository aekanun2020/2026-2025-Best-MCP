# คู่มือทดสอบ RAG MCP Server (Streamable HTTP)

คู่มือนี้สอนการทดสอบ MCP server แบบ **Streamable HTTP transport** (stateless) ตั้งแต่เริ่มจน search ได้ผลจริง ทุกคำสั่ง **คัดลอกไปวางใน Terminal ได้เลย** และผลลัพธ์ที่แสดงในคู่มือคือ output จริงจาก server

> **สิ่งที่ต่างจากเวอร์ชัน SSE เดิม (อ่านก่อน):**
> เวอร์ชันนี้เป็น **Streamable HTTP** ไม่ใช่ HTTP+SSE แบบเก่า ความต่างที่สำคัญ:
>
> | เรื่อง | SSE เก่า | Streamable HTTP (ตัวนี้) |
> |---|---|---|
> | จำนวน endpoint | 2 (`/sse` + `/messages`) | **1 endpoint เดียว** (`/mcp`) |
> | จำนวน Terminal | 2 (เปิด stream ค้าง + ส่งคำสั่ง) | **1 Terminal** พอ |
> | session | ต้องจด `session_id` จาก stream | **stateless** — ไม่ต้องมี session |
> | รับผลลัพธ์ | ไปโผล่อีก Terminal | **กลับมาในคำสั่งเดียวกัน** |
>
> ถ้าคุณเคยใช้คู่มือ SSE เดิม ให้ลืม `/sse`, `/messages?session_id=...` และการเปิด 2 Terminal ไปได้เลย

---

## ภาพรวม: ทดสอบ 5 ขั้น

1. ตรวจว่า server พร้อม (`/health`)
2. Initialize connection (`initialize`)
3. ดูรายการ tools ที่มี (`tools/list`)
4. เพิ่มเอกสารเข้าระบบ (`add_directory`)
5. ค้นหาเอกสาร (`search_documentation`) — ทดสอบทั้ง 3 โหมด

> ทั้งหมดนี้ใช้ **Terminal เดียว** ไม่ต้องเปิด stream ค้างไว้

---

## เตรียมตัวก่อน

ให้แน่ใจว่า server รันอยู่ (ถ้ายังไม่รัน ดู `README.md` หัวข้อ Installation):

```bash
cd rag-mcp-server-streamablehttp
./start_docker.sh        # Mac/Linux
# หรือ double-click start_docker.bat บน Windows
```

ทุกคำสั่งในคู่มือนี้ยิงไปที่ `http://localhost:8000/mcp` (เปลี่ยน host/port ได้ถ้าคุณ map ต่างไป)

> **เคล็ดลับ:** ทุกคำสั่งในคู่มือนี้แนบ header 2 ตัวเสมอ
> ```
> -H "Content-Type: application/json"
> -H "Accept: application/json, text/event-stream"
> ```
> Server ตัวนี้เป็น stateless แบบผ่อนปรน — POST ที่ไม่มี `Accept: text/event-stream` ก็ยังทำงานได้ แต่แนะนำให้แนบไว้เสมอเพื่อให้ตรงมาตรฐาน MCP และใช้กับ client อื่นได้ทันที

---

## ขั้นที่ 1 — ตรวจว่า Server พร้อมใช้งาน

```bash
curl http://localhost:8000/health
```

**ผลลัพธ์ที่คาดหวัง:**

```json
{"status":"healthy","service":"pyragdoc-mcp-server"}
```

> ✅ เห็น `"status":"healthy"` = server พร้อม
> หมายเหตุ: response นี้ **ไม่มี** field `"transport"` แล้ว (ต่างจากสไลด์ SSE เก่าที่ขึ้น `"transport":"sse"`)

---

## ขั้นที่ 2 — Initialize Connection

จับมือ (handshake) กับ server ตามมาตรฐาน MCP:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

**ผลลัพธ์ที่คาดหวัง:**

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25","capabilities":{"tools":{},"resources":{},"prompts":{}},"serverInfo":{"name":"pyragdoc-mcp-server","version":"1.0.0"}}}
```

> ✅ `protocolVersion` คืน `2025-11-25` = handshake สำเร็จ
> เนื่องจากเป็น **stateless** จึงไม่ต้องเก็บ session id ไปขั้นถัดไป — ทุกคำสั่งยิงตรงไป `/mcp` ได้เลย

---

## ขั้นที่ 3 — ดูรายการ Tools ที่มี (4 tools)

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

จะเห็น **4 tools**:

| Tool | หน้าที่ | arguments |
|------|--------|-----------|
| `search_documentation` | ค้นหาเอกสาร | `query` (จำเป็น), `limit` (default 5), `search_mode` (`semantic`/`bm25`/`hybrid`, default `hybrid`) |
| `list_sources` | ลิสต์ source ทั้งหมดที่เก็บอยู่ | — |
| `add_directory` | เพิ่มไฟล์ทั้งโฟลเดอร์เข้าระบบ | `path` (จำเป็น) |
| `add_context` | เพิ่ม text content ตรงๆ เข้า RAG store | `content` (จำเป็น), `title`, `source` (default `agent_context`), `metadata` |

> **หมายเหตุเรื่อง `search_mode`:** ใน `inputSchema` ของ `tools/list` จะเห็นแค่ `query` + `limit` แต่ `search_mode` **ส่งเข้าไปได้จริง** ผ่าน `arguments` (server รับด้วย `**arguments`) — ดูตัวอย่างในขั้นที่ 5

---

## ขั้นที่ 4 — เพิ่มเอกสารเข้าระบบ

ก่อน search ต้องมีเอกสารในระบบก่อน วิธีที่ง่ายสุดคือ `add_directory` ชี้ไปที่โฟลเดอร์เอกสารใน container (`/home/mcpuser/documents` มีไฟล์ตัวอย่างให้แล้ว):

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add_directory","arguments":{"path":"/home/mcpuser/documents"}}}'
```

**ผลลัพธ์ที่คาดหวัง (ตัวอย่างจริง):**

```
Directory Processing Results:

Processed 16 files successfully
Failed to process 0 files
Skipped 0 unsupported files
Added 112 total chunks to the database
...
```

> ⏱️ **ครั้งแรกจะช้า** เพราะต้องสร้าง embedding ทุก chunk (Ollama cold start) ถ้า `curl` timeout ฝั่ง client แต่ server ยัง healthy = มันยัง ingest อยู่เบื้องหลัง รอสักครู่แล้วเช็คด้วย `list_sources`

ตรวจว่าเอกสารเข้าระบบแล้ว:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"list_sources","arguments":{}}}'
```

จะเห็นรายการ source เช่น `customerservice-policy.md`, `loan-analysis-summary.md` เป็นต้น

### ทางเลือก: เพิ่ม text ตรงๆ ด้วย `add_context`

ถ้าอยากเพิ่มข้อความสั้นๆ โดยไม่ต้องมีไฟล์ (เช่น context จาก agent):

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"add_context","arguments":{"content":"การคืนสินค้าประเภทอิเล็กทรอนิกส์ทำได้ภายใน 7 วัน","title":"นโยบายย่อ","source":"demo"}}}'
```

**ผลลัพธ์ที่คาดหวัง:**

```
Successfully added context to database:
- Title: นโยบายย่อ
- Source: demo
- Chunks created: 1
- Total characters: 48
```

---

## ขั้นที่ 5 — ค้นหาเอกสาร (Hybrid / BM25 / Semantic)

หัวใจของระบบคือ search ซึ่งทำได้ **3 โหมด** ลองทั้งสามด้วย query เดียวกันเพื่อเห็นความต่าง

### 5.1 Hybrid (ค่าเริ่มต้น — แนะนำ)

รวม BM25 (คำตรง) + Semantic (ความหมาย) แล้วหลอมด้วย RRF — ไม่ต้องใส่ `search_mode`:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"search_documentation","arguments":{"query":"นโยบายคืนสินค้า","limit":2}}}'
```

**ผลลัพธ์ที่คาดหวัง (ตัวอย่างจริง):**

```
[1] customerservice-policy (Score: 0.02)
Source: /home/mcpuser/documents/customerservice-policy.md

... ## 3. กระบวนการคืนสินค้า ลูกค้ามีสิทธิ์ขอคืนสินค้าภายในระยะเวลาที่กำหนด ...
```

### 5.2 BM25 (keyword search อย่างเดียว)

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"search_documentation","arguments":{"query":"นโยบายคืนสินค้า","limit":2,"search_mode":"bm25"}}}'
```

**ตัวอย่างจริง:** `[1] customerservice-policy (Score: 1.00)` — คะแนนสูงเพราะ query มีคำตรงกับเอกสาร

### 5.3 Semantic (vector search อย่างเดียว)

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"search_documentation","arguments":{"query":"นโยบายคืนสินค้า","limit":2,"search_mode":"semantic"}}}'
```

**ตัวอย่างจริง:** `[1] loan-analysis-summary (Score: 0.66)` — semantic อาจคืนเอกสารที่ใกล้เคียงด้าน "ความหมาย" ไม่จำเป็นต้องมีคำตรง

---

## เข้าใจ Score ของแต่ละโหมด

ค่า Score มาจากคนละสเกล **เทียบข้ามโหมดตรงๆ ไม่ได้** ดูในบริบทของโหมดเดียวกันเท่านั้น:

| โหมด | สเกลของ Score | ความหมาย |
|------|--------------|----------|
| `semantic` | 0–1 (cosine similarity) | ยิ่งใกล้ 1 ยิ่งใกล้เคียงด้านความหมาย เช่น 0.66 |
| `bm25` | normalize 0–1 (เทียบกับ max ในชุดผล) | อันดับ 1 มักได้ 1.00, ตัวถัดมาลดลงตามความเกี่ยวข้องของคำ |
| `hybrid` | RRF score (เล็ก เช่น 0.02) | **อย่าตกใจที่ค่าน้อย** — RRF ให้คะแนนจาก "อันดับ" ของแต่ละ retriever ไม่ใช่ similarity โดยตรง สิ่งที่สำคัญคือ **ลำดับ** ไม่ใช่ค่าตัวเลข |

> ทำไม hybrid score ถึงดูเล็ก? RRF (Reciprocal Rank Fusion) คำนวณจาก `1/(k+rank)` โดย `k=60` ดังนั้นเอกสารอันดับ 1 จาก 2 retriever จะได้ราว `1/61 + 1/61 ≈ 0.033` — ค่าน้อยเป็นเรื่องปกติ ใช้เพื่อ **จัดลำดับ** เท่านั้น

---

## ดู log เพื่อยืนยันว่า Hybrid ทำงานจริง

ดู log สดของ server:

```bash
docker compose logs -f mcp-server
```

เมื่อยิง search แบบ hybrid จะเห็น log ครบ 3 จังหวะ ยืนยันว่าทั้ง sparse + dense ทำงาน:

```
- pyragdoc.core.search - INFO - Search request: query='...', limit=5, mode=hybrid
- pyragdoc.core.bm25   - INFO - BM25 search returned 10 results (max_score=4.22)
- httpx - INFO - HTTP Request: POST http://ollama:11434/api/embeddings "200 OK"   ← dense embedding
- httpx - INFO - HTTP Request: POST http://qdrant:6333/.../points/query "200 OK"  ← dense search
- pyragdoc.core.rrf    - INFO - RRF combined 2 lists into 5 results
- pyragdoc.core.search - INFO - Hybrid search returned 5 results (BM25: 10, Semantic: 10)
```

บรรทัด `Hybrid search returned 5 results (BM25: 10, Semantic: 10)` = ยืนยันว่า **ทั้ง BM25 (sparse) และ Semantic (dense) คืนผลคนละ 10 รายการ แล้วถูกหลอมด้วย RRF เหลือ 5** — นี่คือหลักฐานว่า hybrid ทำงานจริง ไม่ได้ fallback เป็น semantic อย่างเดียว

---

## ทดสอบทั้งหมดในคำสั่งเดียว (script)

ในโฟลเดอร์มีสคริปต์ทดสอบครบทุก tool อยู่แล้ว:

```bash
python3 test_all_tools.py
```

จะรัน health → initialize → tools/list → ทุก tool และสรุปผ่าน/ไม่ผ่าน

---

## แก้ปัญหาที่พบบ่อย (Troubleshooting)

| อาการ | สาเหตุ | วิธีแก้ |
|------|--------|--------|
| `405 Method Not Allowed` ตอน `GET /mcp` | `/mcp` ไม่รับ GET ธรรมดา | ใช้ `POST` (GET สงวนไว้สำหรับเปิด SSE stream ที่ต้องมี `Accept: text/event-stream` เท่านั้น) |
| client บางตัวฟ้องว่าไม่รับ event-stream | ขาด header `Accept` | แนบ `-H "Accept: application/json, text/event-stream"` ให้ตรงมาตรฐาน MCP |
| `No results found` ทั้งที่ ingest แล้ว | ยังไม่ได้เพิ่มเอกสาร / Qdrant ว่าง | ทำขั้นที่ 4 (`add_directory`) ก่อน แล้ว `list_sources` ยืนยัน |
| `add_directory` ค้างนาน/timeout ฝั่ง client | สร้าง embedding ครั้งแรกช้า | server ยังทำงานอยู่ — รอแล้วเช็ค `list_sources` |
| `404 Collection doesn't exist` หลังลบ collection ทิ้ง | collection สร้างตอน startup เท่านั้น | ดู `README.md` หัวข้อ "ดูและล้างข้อมูลใน Qdrant" — ใช้ points-delete แทนการลบทั้ง collection |

---

## อ้างอิงเพิ่มเติม

- `README.md` — การติดตั้ง, usage, การดู/ล้างข้อมูล Qdrant
- `HYBRID_SEARCH_CONFIG.md` — รายละเอียดการตั้งค่า hybrid (BM25 + RRF)
- `ADD_CONTEXT_GUIDE.md` — การใช้ `add_context` แบบละเอียด
- `MCP_CLIENT_INTEGRATION_GUIDE.md` — ต่อ MCP client (เช่น Claude Desktop) เข้ากับ server นี้
