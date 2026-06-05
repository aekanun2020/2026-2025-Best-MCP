# 2026-2025-Best-MCP

รวม **MCP server ที่ดีที่สุด** ที่คัดเลือกมาจากการเปรียบเทียบ MCP server หลายตัว
ในคลัง repo ของ [@aekanun2020](https://github.com/aekanun2020) — ครอบคลุมทั้งงาน **MSSQL execute query** และ **RAG**

## ตัวที่เลือก (จากการเปรียบเทียบ)

ตัวที่ได้จากการคัดเลือกเปรียบเทียบ MCP server หลายตัว — ต้นฉบับเหล่านี้ใช้ **SSE transport** (port `9000/sse`)

| โฟลเดอร์ | ประเภท | transport | ที่มา | เอกสารเปรียบเทียบ |
|---|---|---|---|---|
| [`mssql-mcp-server/`](./mssql-mcp-server) | MSSQL (execute query) | SSE | [2026-customLangFlow-...-mssql](https://github.com/aekanun2020/2026-customLangFlow-and-v5-mcpserver-for-mssql) | [COMPARISON.md](./COMPARISON.md) |
| [`rag-mcp-server-suparag/`](./rag-mcp-server-suparag) | RAG (ดีสุด/ใหม่สุด) | SSE | [SupaRAG](https://github.com/aekanun2020/SupaRAG) | [RAG-COMPARISON.md](./RAG-COMPARISON.md) |
| [`rag-mcp-server-v3/`](./rag-mcp-server-v3) | RAG (เบา + `add_context`) | SSE | [v3-2026-mcp-streamable-sse-rag](https://github.com/aekanun2020/v3-2026-mcp-streamable-sse-rag) | [RAG-COMPARISON.md](./RAG-COMPARISON.md) |

## ตัว Streamable HTTP (ย้าย transport จากตัวที่เลือก)

อีก 2 โฟลเดอร์เป็นเวอร์ชันที่ย้ายจาก SSE มาเป็น **Streamable HTTP transport** (มาตรฐาน MCP ปัจจุบัน — endpoint เดียว `/mcp`, stateless, ไม่บังคับ session) โดยรักษาความสามารถทุกอย่างให้เหมือนต้นฉบับเดิม

| โฟลเดอร์ | ประเภท | endpoint | port (host) | ต้นฉบับ | คู่มือทดสอบ |
|---|---|---|---|---|---|
| [`mssql-mcp-server-streamablehttp/`](./mssql-mcp-server-streamablehttp) | MSSQL (execute query) | `/mcp` | `9000` | [`mssql-mcp-server/`](./mssql-mcp-server) | — |
| [`rag-mcp-server-streamablehttp/`](./rag-mcp-server-streamablehttp) | RAG (Hybrid ไทย) | `/mcp` | `8000` | [`rag-mcp-server-v3/`](./rag-mcp-server-v3) | [TESTING_GUIDE.md](./rag-mcp-server-streamablehttp/TESTING_GUIDE.md) |

---

## 1) MSSQL MCP Server — v5 + Database Context

นำมาจาก [`2026-customLangFlow-and-v5-mcpserver-for-mssql`](https://github.com/aekanun2020/2026-customLangFlow-and-v5-mcpserver-for-mssql)
เหตุผลและตารางเปรียบเทียบเต็มอยู่ที่ [COMPARISON.md](./COMPARISON.md)

### สรุปสั้น ๆ ว่าทำไมตัวนี้ดีที่สุด

- มี tool `get_database_context` ที่ดึง schema + ความสัมพันธ์ (foreign keys) + คู่มือ T-SQL ของทั้ง DB ในครั้งเดียว ทำให้ LLM agent เขียน SQL ได้ถูกต้องก่อนยิง `execute_query_tool` → ลด SQL error
- มี `DatabaseCache` ที่ cache ทั้ง schema และ relationship graph ลดเวลา context จาก ~10 วินาที (cold) เหลือ ~23ms (warm)
- ผ่านการทดสอบจริงด้วยคำถามธุรกิจหลายระดับ ได้คะแนนเฉลี่ยสูง (~98–99.5/100) และ 0 SQL error
- รองรับ SSE transport + Docker + Claude Desktop config พร้อมใช้

## เริ่มใช้งาน

```bash
cd mssql-mcp-server
cp .env.example .env   # ตั้งค่า DB_SERVER / DB_NAME / DB_USER / DB_PASSWORD
docker-compose up      # server (SSE) เปิดที่ http://localhost:9000/sse
```

> อยากได้ transport มาตรฐานปัจจุบัน (Streamable HTTP, endpoint `/mcp`)? ใช้ [`mssql-mcp-server-streamablehttp/`](./mssql-mcp-server-streamablehttp) — เปิดที่ `http://localhost:9000/mcp`

---

## 2) RAG MCP Server — ตัวที่เลือกจากการเปรียบเทียบ 2 ตัว (เด่นคนละด้าน)

รายละเอียดและตารางเปรียบเทียบ RAG ทั้ง 5 ตัวอยู่ที่ [RAG-COMPARISON.md](./RAG-COMPARISON.md)

- **[`rag-mcp-server-suparag/`](./rag-mcp-server-suparag)** — ดีสุด/ใหม่สุด เน้น "indexing ฉลาด":
  Contextual Retrieval ของ Anthropic + OpenSearch (dual index) + BGE-M3 + Qwen + Streamlit UI
- **[`rag-mcp-server-v3/`](./rag-mcp-server-v3)** — เบากว่า (Qdrant) เน้น "ยืดหยุ่นตอนใช้งาน":
  มี tool `add_context` ให้ agent จดความรู้เข้าฐาน RAG เองระหว่างสนทนา (ตัวอื่นไม่มี)

เลือกใช้: อยากแม่น/พร้อม production → SupaRAG; อยากเบา/ให้ agent จดความรู้เอง → v3

> **หมายเหตุ:** ถ้าต้องการ RAG บน transport มาตรฐานปัจจุบัน มี [`rag-mcp-server-streamablehttp/`](./rag-mcp-server-streamablehttp) — ย้าย v3 (Hybrid + `add_context`) มาเป็น Streamable HTTP (endpoint `/mcp`, port `8000`) พร้อม Qdrant + Ollama ใน compose เดียว มีคู่มือทดสอบ copy คำสั่งได้ที่ [TESTING_GUIDE.md](./rag-mcp-server-streamablehttp/TESTING_GUIDE.md)
