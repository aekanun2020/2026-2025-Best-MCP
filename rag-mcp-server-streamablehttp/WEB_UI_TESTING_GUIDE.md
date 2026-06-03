# Web UI Testing Guide - Hybrid Search

## Overview
คู่มือนี้อธิบายวิธีทดสอบ Hybrid Search ผ่าน web UI ที่เชื่อมต่อกับ MCP server

## Search Modes Available

MCP server รองรับ 3 โหมดการค้นหา:

1. **`semantic`** - Dense vector search (เดิม)
   - ค้นหาตามความหมาย/แนวคิด
   - ใช้ embeddings จาก nomic-embed-text

2. **`bm25`** - Sparse keyword search (ใหม่)
   - ค้นหาตาม exact matching
   - เหมาะกับเลขข้อ, ตัวเลขไทย, คำย่อ

3. **`hybrid`** - Combined search (default, ใหม่)
   - รวมผลลัพธ์จากทั้ง semantic และ BM25
   - ใช้ Reciprocal Rank Fusion (RRF) ในการรวมคะแนน
   - **โหมดนี้เป็น default** ถ้าไม่ระบุ search_mode

## How to Test on Web UI

### Method 1: Using Default (Hybrid Mode)
ถ้า web UI ไม่มีตัวเลือก search_mode, มันจะใช้ **hybrid mode** โดยอัตโนมัติ

```
Query: "ข้อ ๒๑"
→ จะได้ผลลัพธ์จาก hybrid search (BM25 + semantic)
```

### Method 2: Specifying Search Mode
ถ้า web UI รองรับการส่ง parameter, ให้ส่ง `search_mode` ไปด้วย:

**Example API Call:**
```json
{
  "query": "ข้อ ๒๑",
  "limit": 5,
  "search_mode": "hybrid"
}
```

**Available values:**
- `"semantic"` - semantic search only
- `"bm25"` - BM25 search only  
- `"hybrid"` - combined (default)

## Test Queries

### 1. Thai Section Numbers (BM25 should excel)
```
Query: "ข้อ ๘๖"
Expected: ควรเจอข้อ ๘๖ ในอันดับต้นๆ
```

```
Query: "ข้อ ๒๑"
Expected: ควรเจอข้อ ๒๑ ในอันดับต้นๆ
```

### 2. Thai Numerals Only (BM25 should excel)
```
Query: "๒๑"
Expected: ควรเจอเอกสารที่มี "๒๑" หรือ "ข้อ ๒๑"
```

### 3. Thai Abbreviations (BM25 should excel)
```
Query: "ก.พ.ว."
Expected: ควรเจอเอกสารที่มี "ก.พ.ว." (คณะกรรมการพิจารณาวิทยฐานะ)
```

### 4. Conceptual Queries (Semantic should excel)
```
Query: "การแต่งตั้งตำแหน่งทางวิชาการ"
Expected: ควรเจอเอกสารเกี่ยวกับการแต่งตั้งตำแหน่ง
```

### 5. Mixed Queries (Hybrid should excel)
```
Query: "ข้อ ๘๖ การแต่งตั้ง"
Expected: ควรเจอข้อ ๘๖ และเอกสารเกี่ยวกับการแต่งตั้ง
```

## Expected Improvements

### Before (Semantic Only)
- ❌ ค้นหา "ข้อ ๒๑" → ไม่เจอหรือเจอผิด
- ❌ ค้นหา "๒๑" → ไม่เจอ
- ❌ ค้นหา "ก.พ.ว." → ไม่เจอ

### After (Hybrid Search)
- ✅ ค้นหา "ข้อ ๒๑" → เจอข้อ ๒๑ อันดับต้นๆ
- ✅ ค้นหา "๒๑" → เจอเอกสารที่มี ๒๑
- ✅ ค้นหา "ก.พ.ว." → เจอเอกสารที่มี ก.พ.ว.
- ✅ ค้นหาแนวคิด → ยังคงทำงานได้ดีเหมือนเดิม

## Checking Server Logs

ถ้าต้องการดู logs เพื่อ debug:

```bash
# ดู logs ของ pyragdoc container
docker-compose logs -f pyragdoc

# ดูว่า BM25 index ถูกสร้างหรือยัง
docker-compose logs pyragdoc | grep "BM25"
```

คุณควรเห็น log แบบนี้:
```
INFO - Building BM25 index from Qdrant documents...
INFO - Loaded 7 documents from Qdrant
INFO - BM25 index built successfully with 7 documents
```

## Troubleshooting

### ถ้าผลลัพธ์ไม่ดีขึ้น
1. ตรวจสอบว่า server restart แล้วหรือยัง
2. ตรวจสอบว่า BM25 index ถูกสร้างหรือยัง (ดู logs)
3. ลอง query ด้วย search_mode แต่ละแบบแยกกัน

### ถ้า web UI ไม่รองรับ search_mode parameter
- ไม่เป็นไร! Default คือ hybrid mode อยู่แล้ว
- ผลลัพธ์ที่ได้จะเป็น hybrid search โดยอัตโนมัติ

### ถ้าต้องการเปลี่ยน default mode
แก้ไขใน `app/mcp_server.py`:
```python
search_mode: str = "hybrid"  # เปลี่ยนเป็น "semantic" หรือ "bm25" ได้
```

## Performance Notes

- **BM25 Index**: In-memory, rebuilt on startup
- **Index Size**: ~1-5 MB per 1,000 documents
- **Build Time**: ~0.1s per 1,000 documents
- **Current**: 7 documents (~0.007 MB, ~0.07s)

## Next Steps

1. ทดสอบ queries ข้างบนบน web UI
2. เปรียบเทียบผลลัพธ์กับเดิม
3. ถ้าผลลัพธ์ดีขึ้น → ✅ Success!
4. ถ้ามีปัญหา → ดู logs และ troubleshooting

---

**Note**: ถ้า web UI ของคุณเป็น custom client, อาจต้องแก้ไข client code เพื่อส่ง `search_mode` parameter ไปด้วย แต่ถ้าไม่ส่ง ก็จะใช้ hybrid mode (default) อยู่แล้ว
