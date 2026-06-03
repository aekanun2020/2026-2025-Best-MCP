# MCP Client Integration Guide - Hybrid Search

## สรุปสำหรับ Web UI / MCP Client Developer

เอกสารนี้อธิบายการเปลี่ยนแปลงของ MCP server ที่เพิ่ม **Hybrid Search** (BM25 + Semantic Search) และวิธีการใช้งานจาก client

---

## 📋 สิ่งที่เปลี่ยนแปลง

### ✅ Backward Compatible
- **ไม่มีการเปลี่ยนแปลงที่ทำลาย API เดิม**
- Client code เดิมยังทำงานได้ปกติ
- เพิ่ม parameter ใหม่ที่เป็น optional

### 🆕 Parameter ใหม่: `search_mode`

Tool `search_documentation` มี parameter ใหม่:

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "ข้อ ๒๑",
    "limit": 5,
    "search_mode": "hybrid"  // ← NEW (optional)
  }
}
```

**ค่าที่รองรับ:**
- `"semantic"` - Dense vector search (เดิม)
- `"bm25"` - Sparse keyword search (ใหม่)
- `"hybrid"` - Combined search with RRF (ใหม่, **default**)

**Default:** ถ้าไม่ระบุ `search_mode`, จะใช้ `"hybrid"` โดยอัตโนมัติ

---

## 🚀 การใช้งาน

### Option 1: ไม่ต้องแก้ไข Client (แนะนำ)

**ไม่ต้องทำอะไรเลย!** Server จะใช้ hybrid mode โดยอัตโนมัติ

```javascript
// Client code เดิม - ยังทำงานได้
const result = await mcpClient.callTool("search_documentation", {
  query: "ข้อ ๒๑",
  limit: 5
  // ไม่ต้องระบุ search_mode, จะใช้ hybrid โดยอัตโนมัติ
});
```

### Option 2: เพิ่ม Mode Selector (Optional)

ถ้าต้องการให้ user เลือก search mode:

```javascript
// เพิ่ม dropdown/radio buttons ใน UI
const searchMode = userSelection; // "semantic", "bm25", or "hybrid"

const result = await mcpClient.callTool("search_documentation", {
  query: userQuery,
  limit: 5,
  search_mode: searchMode  // ส่ง mode ที่ user เลือก
});
```

**UI Suggestion:**
```
Search Mode: 
○ Semantic (ค้นหาตามความหมาย)
○ BM25 (ค้นหาคำที่ตรงกัน)
● Hybrid (รวมทั้งสอง) ← Default
```

---

## 📊 ผลลัพธ์ที่คาดหวัง

### Semantic Mode
- ✅ ดีสำหรับ: คำถามเชิงแนวคิด, ความหมาย
- ❌ อ่อนสำหรับ: เลขข้อ, ตัวเลขไทย, คำย่อ

**ตัวอย่าง:**
```
Query: "การแต่งตั้งตำแหน่งทางวิชาการ"
Result: ✅ เจอเอกสารเกี่ยวกับการแต่งตั้ง
```

### BM25 Mode
- ✅ ดีสำหรับ: เลขข้อ, ตัวเลขไทย, คำย่อ, exact matching
- ❌ อ่อนสำหรับ: คำถามเชิงแนวคิด

**ตัวอย่าง:**
```
Query: "ข้อ ๘๖"
Result: ✅ เจอข้อ ๘๖ โดยตรง (Score: 1.00)
```

### Hybrid Mode (Default)
- ✅ ดีสำหรับ: **ทุกประเภทคำถาม**
- ✅ รวมจุดแข็งของทั้งสองโหมด
- ✅ Graceful degradation (ถ้าโหมดหนึ่ง fail ใช้อีกโหมด)

**ตัวอย่าง:**
```
Query: "ข้อ ๘๖ การแต่งตั้ง"
Result: ✅ เจอทั้ง "ข้อ ๘๖" และเอกสารเกี่ยวกับ "การแต่งตั้ง"
```

---

## ⚠️ สิ่งที่ต้องรู้

### 1. RRF Scores จะต่ำ
Hybrid mode ใช้ Reciprocal Rank Fusion (RRF) ซึ่งให้คะแนนต่ำ (0.01-0.05)

**นี่เป็นเรื่องปกติ!** ให้ดูที่:
- ✅ **ลำดับการจัดอันดับ** (ranking order) - ถูกต้อง
- ❌ **ค่าคะแนนสัมบูรณ์** (absolute score) - ต่ำแต่ไม่สำคัญ

**ตัวอย่าง:**
```json
{
  "results": [
    {"text": "ข้อ ๘๖...", "score": 0.02},  // ← อันดับ 1 (ถูกต้อง)
    {"text": "ข้อ ๑...", "score": 0.02},   // ← อันดับ 2
    {"text": "ข้อ ๒...", "score": 0.01}    // ← อันดับ 3
  ]
}
```

**คำแนะนำ:**
- ไม่ต้องกรองผลลัพธ์ด้วย score threshold
- แสดงผลตามลำดับที่ได้มา
- ถ้าต้องการแสดงคะแนน อาจ normalize เป็น % หรือ ⭐

### 2. Response Format ไม่เปลี่ยน
Format ของ response ยังเหมือนเดิม:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[1] formatted_regulations (Score: 0.02)\nSource: ...\n\nข้อ ๘๖..."
      }
    ]
  }
}
```

### 3. Error Handling
ถ้าส่ง `search_mode` ที่ไม่ถูกต้อง:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "Invalid search_mode: must be 'semantic', 'bm25', or 'hybrid'"
  }
}
```

---

## 🧪 การทดสอบ

### Test Queries ที่แนะนำ

**1. Thai Section Numbers (ทดสอบ BM25)**
```
Query: "ข้อ ๘๖"
Expected: เจอข้อ ๘๖ ในอันดับต้นๆ
```

**2. Thai Numerals (ทดสอบ BM25)**
```
Query: "๒๑"
Expected: เจอเอกสารที่มี ๒๑
```

**3. Thai Abbreviations (ทดสอบ BM25)**
```
Query: "ก.พ.ว."
Expected: เจอเอกสารที่มี ก.พ.ว.
```

**4. Conceptual (ทดสอบ Semantic)**
```
Query: "การแต่งตั้งตำแหน่งทางวิชาการ"
Expected: เจอเอกสารเกี่ยวกับการแต่งตั้ง
```

**5. Mixed (ทดสอบ Hybrid)**
```
Query: "ข้อ ๘๖ การแต่งตั้ง"
Expected: เจอทั้ง exact match และ conceptual
```

### ตัวอย่าง Code สำหรับทดสอบ

```javascript
// Test function
async function testHybridSearch() {
  const testQueries = [
    { query: "ข้อ ๘๖", mode: "hybrid", description: "Thai section number" },
    { query: "๒๑", mode: "hybrid", description: "Thai numeral" },
    { query: "ก.พ.ว.", mode: "hybrid", description: "Thai abbreviation" },
    { query: "การแต่งตั้ง", mode: "semantic", description: "Conceptual" }
  ];

  for (const test of testQueries) {
    console.log(`\nTesting: ${test.description}`);
    console.log(`Query: "${test.query}", Mode: ${test.mode}`);
    
    const result = await mcpClient.callTool("search_documentation", {
      query: test.query,
      limit: 3,
      search_mode: test.mode
    });
    
    console.log("Results:", result);
  }
}
```

---

## 📝 Checklist สำหรับ Integration

### Phase 1: Basic Integration (ไม่ต้องแก้ code)
- [ ] Deploy MCP server version ใหม่
- [ ] ทดสอบ client เดิมว่ายังทำงานได้
- [ ] ทดสอบ queries ที่เคยมีปัญหา (เลขข้อ, ตัวเลขไทย)
- [ ] ตรวจสอบว่าผลลัพธ์ดีขึ้น

### Phase 2: Advanced Integration (Optional)
- [ ] เพิ่ม mode selector ใน UI
- [ ] เพิ่ม tooltip อธิบายแต่ละ mode
- [ ] ปรับการแสดงผล score (normalize หรือซ่อน)
- [ ] เพิ่ม analytics tracking สำหรับ mode usage

### Phase 3: Optimization (Optional)
- [ ] A/B testing ระหว่าง semantic vs hybrid
- [ ] รวบรวม user feedback
- [ ] ปรับ default mode ตาม use case
- [ ] เพิ่ม smart mode selection (auto-detect query type)

---

## 🔧 Technical Details

### MCP Server Endpoint
```
POST http://localhost:8000/mcp
Content-Type: application/json
MCP-Protocol-Version: 2024-11-05
```

### Tool Schema
```json
{
  "name": "search_documentation",
  "description": "Search through stored documentation",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "limit": {
        "type": "number",
        "default": 5,
        "description": "Maximum number of results"
      },
      "search_mode": {
        "type": "string",
        "enum": ["semantic", "bm25", "hybrid"],
        "default": "hybrid",
        "description": "Search mode: semantic (meaning-based), bm25 (exact matching), or hybrid (combined)"
      }
    },
    "required": ["query"]
  }
}
```

### Performance
- **Semantic only**: ~100-300ms
- **BM25 only**: ~10-50ms
- **Hybrid**: ~150-400ms

---

## 📚 เอกสารเพิ่มเติม

1. **`TEST_RESULTS_SUMMARY.md`** - ผลการทดสอบโดยละเอียด
2. **`CURL_TESTING_GUIDE.md`** - วิธีทดสอบด้วย curl
3. **`WEB_UI_TESTING_GUIDE.md`** - คู่มือทดสอบบน web UI
4. **`HYBRID_SEARCH_CONFIG.md`** - การ tune performance

---

## 🆘 Support & Troubleshooting

### ปัญหาที่พบบ่อย

**Q: ผลลัพธ์ไม่ดีขึ้น?**
A: ตรวจสอบว่า:
1. Server restart แล้วหรือยัง
2. BM25 index ถูกสร้างหรือยัง (ดู logs)
3. ใช้ hybrid mode หรือยัง

**Q: Score ต่ำมาก (0.02)?**
A: นี่เป็นเรื่องปกติของ RRF! ดูที่ ranking order แทน

**Q: Client เดิมยังทำงานได้ไหม?**
A: ได้! 100% backward compatible

**Q: ต้องแก้ client code ไหม?**
A: ไม่ต้อง! แต่ถ้าต้องการ mode selector ต้องเพิ่ม UI

### ติดต่อ
- ดู server logs: `docker-compose logs -f pyragdoc`
- ตรวจสอบ Qdrant: `./check-qdrant.sh`
- ทดสอบด้วย curl: `./test-mcp-tools-curl.sh`

---

## ✅ Summary

**สิ่งที่ต้องรู้:**
1. ✅ Backward compatible - client เดิมยังใช้ได้
2. ✅ Default เป็น hybrid mode - ไม่ต้องแก้ code
3. ✅ เพิ่ม `search_mode` parameter (optional)
4. ⚠️ RRF scores ต่ำ - แต่ ranking ถูกต้อง
5. 🚀 ผลลัพธ์ดีขึ้นสำหรับ Thai queries

**Action Items:**
1. Deploy server version ใหม่
2. ทดสอบ client เดิม
3. ทดสอบ queries ที่เคยมีปัญหา
4. (Optional) เพิ่ม mode selector

---

**Version:** 1.0.0  
**Date:** 2026-01-24  
**Status:** ✅ Production Ready
