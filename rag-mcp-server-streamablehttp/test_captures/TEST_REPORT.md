# RAG MCP Server (Streamable HTTP) — Test Report

ทดสอบ end-to-end จริงบน Docker โดยรัน **Qdrant + Ollama** เป็น service ภายนอก แล้วให้ container ของ RAG MCP server ต่อเข้าไปผ่าน `host.docker.internal`

- **Transport:** Streamable HTTP (single endpoint `/mcp`), **stateless**
- **Protocol version:** `2025-11-25`
- **Embedding:** Ollama `nomic-embed-text` (vector size 768)
- **Vector DB:** Qdrant (collection `documentation`)
- **Container:** `rag-mcp-streamable-http`, expose port `9000` (ในการทดสอบนี้ map host port `9002` เพราะ host `9000` ถูกใช้งานอยู่)

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

## Captures

- `01_all_tools_e2e.png` — ผลรัน `test_all_tools.py` (9/9 PASS)
- `02_protocol_raw.png` — raw `initialize` + `tools/list` (4 tools) + GET 405
- `03_docker_run.png` — docker ps + log จริงตอน ingest เข้า Qdrant ผ่าน Ollama, session=None, GET 405, DELETE 204

## How to reproduce

```bash
# 1) external services
docker run -d --name pyrag-qdrant -p 6333:6333 qdrant/qdrant:latest
docker run -d --name pyrag-ollama -p 11434:11434 ollama/ollama:latest
docker exec pyrag-ollama ollama pull nomic-embed-text

# 2) build + run this server (uses .env.example -> .env)
./start_docker.sh        # Mac    (Windows: double-click start_docker.bat)

# 3) run the test suite
python test_all_tools.py http://localhost:9000/mcp
```
