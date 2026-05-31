# การเปรียบเทียบ MCP Server for RAG — ทำไมเลือก SupaRAG และ v3

เอกสารนี้อธิบายว่าทำไม repo นี้จึงเก็บ RAG MCP server ไว้ **2 ตัว** คือ
[`rag-mcp-server-suparag/`](./rag-mcp-server-suparag) และ [`rag-mcp-server-v3/`](./rag-mcp-server-v3)
จากการเปรียบเทียบ RAG server ทั้ง 5 ตัวในคลัง repo

## ผู้เข้าแข่งขัน (RAG MCP server ที่มีอยู่)

ทั้ง 5 ตัวเริ่มจากฐานเดียวกัน ("PyRAGDoc") แล้วต่อยอดขึ้นเรื่อย ๆ จนถึง SupaRAG ที่เปลี่ยนสถาปัตยกรรมใหม่

| รุ่น | repo ต้นทาง | push ล่าสุด | search engine | จุดเด่นที่เพิ่มเข้ามา |
|---|---|---|---|---|
| 1 | [2026-mcp-streamable-sse-rag](https://github.com/aekanun2020/2026-mcp-streamable-sse-rag) | 27 ม.ค. 2026 | Qdrant + BM25 + RRF | เริ่มมี Hybrid Search + ภาษาไทย, 98 tests |
| 2 | [2026-mcp-sse-rag](https://github.com/aekanun2020/2026-mcp-sse-rag) | 27 ม.ค. 2026 | Qdrant (semantic ล้วน) | รุ่น SSE-only เล็ก/เบา — **ไม่มี hybrid** |
| 3 | [v2-2026-mcp-sse-rag-fixed](https://github.com/aekanun2020/v2-2026-mcp-sse-rag-fixed) | 31 ม.ค. 2026 | Qdrant + BM25 + RRF | รุ่นแก้บั๊ก + ระบุ stable commit |
| **4. v3** ✅ | [v3-2026-mcp-streamable-sse-rag](https://github.com/aekanun2020/v3-2026-mcp-streamable-sse-rag) | 1 ก.พ. 2026 | Qdrant + BM25 + RRF | เพิ่ม tool **`add_context`** (agent เก็บความรู้เองได้) |
| **5. SupaRAG** ✅ | [SupaRAG](https://github.com/aekanun2020/SupaRAG) | **30 พ.ค. 2026** | **OpenSearch (dual index) + BGE-M3 + Qwen** | **Contextual Retrieval ของ Anthropic** |

## ตารางเปรียบเทียบความสามารถ

| ความสามารถ | SupaRAG ✅ | v3 ✅ | รุ่น 1 | รุ่น 2 | รุ่น 3 |
|---|:---:|:---:|:---:|:---:|:---:|
| Hybrid Search (BM25 + Vector + RRF) | ✅ | ✅ | ✅ | ❌ (semantic ล้วน) | ✅ |
| เลือก search_mode (semantic/bm25/hybrid) | — | ✅ | ✅ | ❌ | ✅ |
| **Contextual Retrieval (Anthropic)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **tool `add_context` (agent จดความรู้เอง)** | ❌ | ✅ | ❌ | ❌ | ❌ |
| `generate_answer` (ตอบคำถามพร้อม source) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Vector store | OpenSearch | Qdrant | Qdrant | Qdrant | Qdrant |
| Embeddings | BGE-M3 (1024 มิติ) | (Qdrant embed) | เดิม | เดิม | เดิม |
| Web UI (Streamlit) | ✅ | ❌ | ❌ | ❌ | ❌ |
| รองรับภาษาไทย / เลขไทย (๑๒๓) | ✅ | ✅ | ✅ | บางส่วน | ✅ |
| MCP spec | 2025-11-25 | เดิม | เดิม | เดิม | เดิม |

## ทำไมเก็บไว้ 2 ตัว (ไม่ใช่ตัวเดียว)

SupaRAG กับ v3 ทำงานคนละปรัชญา และเด่นคนละด้าน จึงเก็บไว้ทั้งคู่

### SupaRAG — ดีที่สุดและใหม่สุด (เน้น "indexing ฉลาด")
- เพิ่ม **Contextual Retrieval ของ Anthropic** — เติมบริบทเข้าไปในแต่ละ chunk *ก่อน* embed
  ช่วยแก้จุดอ่อนคลาสสิกของ RAG ที่ chunk เดี่ยว ๆ ขาดบริบท → recall/ความแม่นสูงขึ้น
- ใช้ **OpenSearch dual index** (vector + BM25 ในระบบเดียว) แทน Qdrant — production-grade, สเกลง่ายกว่า
- **BGE-M3 (1024 มิติ)** + **Qwen 2.5** สร้าง context
- มี **Streamlit Web UI** จัดการเอกสารในตัว, 4 containers พร้อม deploy, MCP spec ใหม่ (2025-11-25)
- ถูกดูแลต่อเนื่องล่าสุด (push 30 พ.ค. 2026 — ใหม่กว่าตัวอื่นหลายเดือน)
- tools: `search_documentation`, `add_documents`, `generate_answer`

### v3 — เบากว่า ติดตั้งง่าย และมี `add_context` (เน้น "ยืดหยุ่นตอนใช้งาน")
- เป็นรุ่นที่ดีที่สุดในสาย PyRAGDoc เดิม: มี hybrid search ครบ + เลือก search_mode ได้
- ใช้ **Qdrant** ซึ่งติดตั้งเบากว่า OpenSearch — เหมาะถ้าไม่อยากรันสแต็กเต็ม
- มี tool พิเศษ **`add_context`** ที่ตัวอื่นไม่มี (รวมถึง SupaRAG):

  ```
  add_context(content, title=None, source="agent_context", metadata=None)
  ```

  ให้ AI agent ป้อนข้อความเข้าฐาน RAG ได้โดยตรง (ไม่ต้องมีไฟล์/URL) โดยมันจะ chunk →
  สร้าง embedding → เก็บลง Qdrant → **อัปเดต BM25 index พร้อมกัน** ทำให้ค้นเจอด้วย hybrid
  search ได้ทันที ใช้เป็น **หน่วยความจำระยะยาวของ agent** ที่จดความรู้ระหว่างสนทนาแล้วค้นเจอครั้งหน้า
- tools: `add_documentation`, `search_documentation` (มี search_mode), `list_sources`, `add_directory`, **`add_context`**

## รุ่นที่ไม่เลือก (ไม่ควรเริ่มงานใหม่)
- **รุ่น 2 (`2026-mcp-sse-rag`)** — `search_documentation(query, limit)` ไม่มี search_mode = semantic ล้วน ไม่มี hybrid → ด้อยสุด
- **รุ่น 1 และ 3** — ถูกแทนที่ด้วย v3 ไปแล้ว เก็บไว้อ้างอิง stable commit ได้ แต่ความสามารถเป็น subset ของ v3

## สรุป

> - อยากได้ RAG ที่ **แม่นสุด / ใหม่สุด / production-ready** → **SupaRAG** (Contextual Retrieval + OpenSearch + UI)
> - อยากได้ตัว **เบา ติดตั้งง่าย (Qdrant)** หรือต้องการให้ **agent จดความรู้เองด้วย `add_context`** → **v3**
>
> ถ้าต้องการรวมข้อดีทั้งสอง สามารถ port tool `add_context` ของ v3 เข้าไปใน SupaRAG ได้

---

แหล่งที่มา:
- [SupaRAG](https://github.com/aekanun2020/SupaRAG) (ตัวที่เลือก — Contextual Retrieval)
- [v3-2026-mcp-streamable-sse-rag](https://github.com/aekanun2020/v3-2026-mcp-streamable-sse-rag) (ตัวที่เลือก — add_context)
- [2026-mcp-streamable-sse-rag](https://github.com/aekanun2020/2026-mcp-streamable-sse-rag) / [v2-2026-mcp-sse-rag-fixed](https://github.com/aekanun2020/v2-2026-mcp-sse-rag-fixed) / [2026-mcp-sse-rag](https://github.com/aekanun2020/2026-mcp-sse-rag) (รุ่นก่อนหน้า)
