# RAG MCP Server (Streamable HTTP) — Test Report

ทดสอบ end-to-end จริงบน Docker — `docker-compose.yml` รันให้ครบทั้ง **Qdrant + Ollama + RAG MCP server** ในคำสั่งเดียว (ตรงกับ rag-mcp-server-v3) — ไม่ต้องติดตั้ง Qdrant/Ollama แยกเอง RAG server ต่อ Qdrant ผ่าน service name ภายใน (`http://qdrant:6333`)

- **Transport:** Streamable HTTP (single endpoint `/mcp`), **stateless**
- **Protocol version:** `2025-11-25`
- **Embedding:** Ollama `nomic-embed-text` (vector size 768)
- **Vector DB:** Qdrant (collection `documentation`)
- **Containers (จาก compose เดียว):** `pyrag-qdrant-streamable` (6333), `pyrag-ollama-streamable` (11434, pull `nomic-embed-text` อัตโนมัติ), `rag-mcp-streamable-http` (**`8000:8000`**) — รันด้วย `docker compose up -d --build` คำสั่งเดียว ทดสอบที่ `http://localhost:8000/mcp`

## Result: 9/9 checks passed

| # | Check | ผล | หมายเหตุ |
|---|-------|-----|---------|
| 1 | `GET /health` | PASS | `{"status":"healthy"}` |
| 2 | `POST /mcp` initialize | PASS | คืน JSON body + header `Mcp-Session-Id`, `protocolVersion=2025-11-25` |
| 3 | `GET /mcp` (ไม่ใส่ `Accept: text/event-stream`) | PASS | คืน **405** ตาม spec |
| 4 | `tools/list` (ไม่ส่ง session id) | PASS | ได้ครบ **4 tools** — ยืนยัน stateless |
| 5 | `tools/call add_context` | PASS | เพิ่ม context ลง RAG store สำเร็จ (1 chunk) |
| 6 | `tools/call list_sources` | PASS | แสดง source `e2e_test` ที่เพิ่งเพิ่ม |
| 7 | `tools/call search_documentation` | PASS | Hybrid Search คืนผลภาษาไทย (score 0.74) |
| 8 | `tools/call add_directory` | PASS | ingest ไฟล์จาก `/home/mcpuser/documents` (1 file) |
| 9 | `DELETE /mcp` | PASS | คืน **204** เมื่อมี session |

## Tools tested (4)

1. `search_documentation` — ค้นหาด้วย Hybrid Search (BM25 + Semantic + RRF) รองรับภาษาไทย
2. `list_sources` — ลิสต์ source ทั้งหมด
3. `add_directory` — ingest ไฟล์ทั้งโฟลเดอร์
4. `add_context` — เพิ่ม text content ตรงๆ (ฟีเจอร์ของ v3 ที่ wire เพิ่มเข้า `tools/list` + dispatch ของ entry point นี้)

## Stateless verification

- `tools/list` และ `tools/call` ทุกตัวยิงโดย **ไม่ส่ง `Mcp-Session-Id`** และ server ยังตอบ JSON ปกติ (log แสดง `session=None`)
- ตรงกับ Streamable HTTP path ของ PyClaw ที่ไม่ส่ง session id กลับ → ต่อได้ทันทีโดยไม่ต้องแก้

## Real-document test (เอกสาร .md จริงจาก repo)

นำไฟล์ `.md` ทั้ง **17 ไฟล์** จาก `rag-mcp-server-v3/` (ทั้งคู่มือ + เอกสาร domain เช่น `customerservice-policy.md`, `dti-calculation-guide.md`, `loan-analysis-summary.md`, `job_announcement.md`, `รายการเอกสารส่ง-Client.md`) ไป ingest แล้วค้นจริง:

| ขั้น | ผล |
|------|-----|
| `add_directory /home/mcpuser/v3docs` | ingest **17 ไฟล์ สำเร็จทั้งหมด, 0 fail** — สร้าง **117 chunks** เข้า Qdrant |
| `list_sources` | แสดง source ครบทั้ง 17 ไฟล์ |
| `search_documentation` (Thai) | "DTI การคำนวณ..." → `dti.md` (score 0.80); "นโยบายบริการลูกค้า" / "customer service policy" → `customerservice-policy.md` (PDPA) |
| `search_documentation` (Eng) | "Ollama setup nomic-embed-text" → `OLLAMA_SETUP.md` (score 0.71); "loan analysis summary" → `loan-analysis-summary.md` |

ยืนยันว่า Hybrid Search ดึงเนื้อหาจริงได้ทั้ง **ภาษาไทยและอังกฤษ** หมายเหตุ: query กว้างๆ บางครั้ง favor `loan-analysis-summary.md` (ไฟล์ใหญ่สุด 48KB → chunk เยอะ) แต่ query ที่เจาะจงคืนเอกสารที่ตรงประเด็นได้ถูกต้อง

## Captures

- `01_all_tools_e2e.png` — ผลรัน `test_all_tools.py` (9/9 PASS)
- `02_protocol_raw.png` — raw `initialize` + `tools/list` (4 tools) + GET 405
- `03_docker_run.png` — docker ps + log จริงตอน ingest เข้า Qdrant ผ่าน Ollama, session=None, GET 405, DELETE 204
- `04_v3docs_ingest_search.png` — ingest เอกสาร .md จริง 17 ไฟล์ (117 chunks) + Hybrid Search คืนผลภาษาไทย/อังกฤษ

## How to reproduce

```bash
# 1) ขึ้นครบทั้ง Qdrant + Ollama + RAG server ในคำสั่งเดียว
#    (ตัว start script จะ copy .env.example -> .env และ build + up ให้)
./start_docker.sh        # Mac    (Windows: double-click start_docker.bat)
# Ollama จะ pull nomic-embed-text ให้อัตโนมัติตอนรันครั้งแรก (~1 นาที)

# 2) run the test suite
python test_all_tools.py http://localhost:8000/mcp
```
