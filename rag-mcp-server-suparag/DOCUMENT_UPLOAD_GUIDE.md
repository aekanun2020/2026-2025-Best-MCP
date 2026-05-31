# คู่มือการวางไฟล์เพื่อนำเข้าระบบ

## 📂 Path สำหรับวางไฟล์

### ใน Host Machine (Mac)
```
2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API/corpus_input/
```

**Full Path:**
```
~/Desktop/test/2026-04-15/2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API/corpus_input/
```

---

### ใน Container (MCP Server)
```
/app/rag/corpus_input/
```

**Volume Mapping:**
```yaml
# docker-compose.yml
volumes:
  - ./AuthenticRAG-Qwen2.5API:/app/rag:ro
```

**อธิบาย:**
- Host: `./AuthenticRAG-Qwen2.5API` → Container: `/app/rag`
- Host: `./AuthenticRAG-Qwen2.5API/corpus_input` → Container: `/app/rag/corpus_input`
- `:ro` = read-only (container อ่านได้อย่างเดียว แก้ไขไม่ได้)

---

## 📝 วิธีการวางไฟล์

### 1. วางไฟล์ใน Host
```bash
cd 2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API/corpus_input/

# วางไฟล์ .md ของคุณที่นี่
cp /path/to/your/document.md .
```

### 2. ตรวจสอบว่าไฟล์อยู่
```bash
ls -la corpus_input/
```

**ตัวอย่าง Output:**
```
1.md      # โรคหัดเยอรมัน (64KB)
2.md      # อหิวาตกโรค (60KB)
44.md     # ต้อกระจก (49KB)
5555.md   # กรดไหลย้อน (59KB)
your-new-document.md  # ← ไฟล์ใหม่ของคุณ
```

### 3. Index ไฟล์เข้าระบบ
```bash
# ใช้ MCP tool: add_documents
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

**หรือใช้ Kiro MCP Client:**
```
add_documents(path="/app/rag/corpus_input")
```

---

## ⚠️ ข้อจำกัดปัจจุบัน

### ปัญหา: Context Generation ต้องใช้ API Key

เนื่องจาก `DASHSCOPE_API_KEY` ถูก comment out แล้ว, การ index เอกสารใหม่จะ **ล้มเหลว** ที่ขั้นตอน context generation:

```python
# authenticRAG.py
def generate_context(self, document_content, chunk_content):
    context = self.call_qwen_api(prompt, max_tokens=100, temperature=0.1)
    # ↑ จะ error: DASHSCOPE_API_KEY not set
```

### วิธีแก้ (3 ทางเลือก)

#### ทางเลือก 1: เปิด API Key ชั่วคราว ✅ แนะนำ
```bash
# 1. Uncomment API key ใน .env
nano .env
# DASHSCOPE_API_KEY=sk-REDACTED_SET_VIA_ENV
# ↓
DASHSCOPE_API_KEY=sk-REDACTED_SET_VIA_ENV

# 2. Restart container
docker-compose restart mcp-server

# 3. Index documents
curl -X POST http://localhost:9001/mcp ...

# 4. Comment out API key อีกครั้ง
nano .env
# DASHSCOPE_API_KEY=sk-REDACTED_SET_VIA_ENV

# 5. Restart container
docker-compose restart mcp-server
```

#### ทางเลือก 2: แก้โค้ดให้ skip context generation
```python
# authenticRAG.py
def generate_context(self, document_content, chunk_content):
    # Skip context generation if API key not available
    if not self.api_key:
        return ""  # Return empty context
    
    prompt = self.get_context_prompt(document_content, chunk_content)
    context = self.call_qwen_api(prompt, max_tokens=100, temperature=0.1)
    return context.strip()
```

**ข้อเสีย:** เอกสารจะไม่มี contextualized content → คุณภาพการค้นหาลดลง

#### ทางเลือก 3: ใช้เอกสารที่ index ไว้แล้ว
ระบบมีเอกสาร 4 ไฟล์ (53 chunks) ที่ index ไว้แล้วใน OpenSearch:
- 1.md - โรคหัดเยอรมัน
- 2.md - อหิวาตกโรค
- 44.md - ต้อกระจก
- 5555.md - กรดไหลย้อน

**ไม่ต้องทำอะไร** - ใช้เอกสารเดิมต่อไป

---

## 📊 ตรวจสอบเอกสารที่ index แล้ว

### ใน OpenSearch
```bash
# ดูจำนวน documents ใน vector index
curl -s http://localhost:9201/anthropic-vector-index/_count | jq

# ดูจำนวน documents ใน BM25 index
curl -s http://localhost:9201/anthropic-bm25-index/_count | jq
```

**ตัวอย่าง Output:**
```json
{
  "count": 53,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  }
}
```

### ดูเอกสารตัวอย่าง
```bash
# ดู document แรก
curl -s http://localhost:9201/anthropic-bm25-index/_search?size=1 | jq '.hits.hits[0]._source'
```

---

## 🔍 ทดสอบการค้นหา

### ค้นหาเอกสารที่มีอยู่
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
        "query": "โรค",
        "limit": 3
      }
    }
  }' | jq -r '.result.content[0].text'
```

**ควรได้ผลลัพธ์:**
- Document doc_16 - เมดไทย
- Document doc_44 - อหิวาตกโรค
- Document doc_42 - เมดไทย categories

---

## 📁 โครงสร้างไฟล์

```
2026-ContextualRAG-MCP-Streamable-HTTP/
├── AuthenticRAG-Qwen2.5API/
│   ├── corpus_input/              ← วางไฟล์ที่นี่!
│   │   ├── 1.md                   ✅ Indexed
│   │   ├── 2.md                   ✅ Indexed
│   │   ├── 44.md                  ✅ Indexed
│   │   ├── 5555.md                ✅ Indexed
│   │   └── your-new-file.md       ← ไฟล์ใหม่
│   ├── authenticRAG.py
│   ├── streamlit_app.py
│   └── ...
├── mcp-server/
│   ├── main.py
│   └── ...
└── docker-compose.yml
```

---

## 🎯 สรุป

### วางไฟล์ที่ไหน?
```
Host: 2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API/corpus_input/
Container: /app/rag/corpus_input/
```

### ไฟล์ประเภทไหน?
- ✅ Markdown files (`.md`)
- ❌ ไฟล์อื่นๆ จะถูกข้าม

### Index อย่างไร?
```bash
# Via MCP tool
add_documents(path="/app/rag/corpus_input")

# หรือ index ไฟล์เดียว
add_documents(path="/app/rag/corpus_input/your-file.md")
```

### ข้อจำกัด?
- ⚠️ ต้องมี `DASHSCOPE_API_KEY` เพื่อสร้าง context
- ⚠️ ถ้าไม่มี API key จะ error ตอน indexing
- ✅ การค้นหาเอกสารเดิมยังใช้งานได้ปกติ

---

## 💡 Tips

### 1. ตั้งชื่อไฟล์ให้เข้าใจง่าย
```
❌ 1.md, 2.md, 44.md
✅ rubella.md, cholera.md, cataract.md
```

### 2. ใช้ Markdown format ที่ดี
```markdown
# หัวข้อหลัก

## หัวข้อย่อย

เนื้อหา...

- รายการ 1
- รายการ 2
```

### 3. แบ่ง chunk ให้เหมาะสม
- Chunk size: 256 characters (ตั้งค่าใน `MarkdownNodeParser`)
- เอกสารยาวจะถูกแบ่งเป็นหลาย chunks
- แต่ละ chunk จะมี contextualized content แยกกัน

### 4. ตรวจสอบก่อน index
```bash
# ดูขนาดไฟล์
ls -lh corpus_input/

# นับจำนวนบรรทัด
wc -l corpus_input/*.md

# ดูเนื้อหาคร่าวๆ
head -20 corpus_input/your-file.md
```

---

## 🔧 Troubleshooting

### ปัญหา: ไฟล์ไม่เห็นใน container
```bash
# ตรวจสอบว่า volume mount ถูกต้อง
docker exec contextual-rag-mcp ls -la /app/rag/corpus_input/
```

### ปัญหา: Permission denied
```bash
# ตรวจสอบ permission
ls -la AuthenticRAG-Qwen2.5API/corpus_input/

# แก้ไข permission (ถ้าจำเป็น)
chmod 644 AuthenticRAG-Qwen2.5API/corpus_input/*.md
```

### ปัญหา: API key error
```bash
# ตรวจสอบว่า API key ถูก comment out หรือไม่
cat .env | grep DASHSCOPE

# ถ้าต้องการ index ต้อง uncomment ก่อน
```
