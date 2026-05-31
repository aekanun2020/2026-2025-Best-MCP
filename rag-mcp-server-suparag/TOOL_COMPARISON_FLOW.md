# เปรียบเทียบ 2 Tools: search_documentation vs generate_answer

## 📊 ภาพรวม

| Feature | search_documentation | generate_answer |
|---------|---------------------|-----------------|
| **จุดประสงค์** | ค้นหาเอกสารที่เกี่ยวข้อง | สร้างคำตอบจากคำถาม |
| **Output** | รายการเอกสาร + Score | คำตอบเป็นประโยค |
| **ใช้ LLM** | ❌ ไม่ใช้ | ✅ ใช้ Qwen API |
| **ใช้ Context** | ❌ ไม่ใช้ | ✅ ใช้ (ถ้า use_context=True) |
| **เหมาะกับ** | ต้องการดูเอกสารต้นฉบับ | ต้องการคำตอบโดยตรง |

---

## 🔍 Tool 1: search_documentation

### Flow Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│ USER INPUT                                                       │
│ query: "โรค"                                                     │
│ limit: 3                                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Hybrid Search                                           │
│ Method: rag_client.hybrid_search(query, k=limit)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ├──────────────┬──────────────┐
                         ▼              ▼              ▼
         ┌───────────────────┐  ┌──────────────┐  ┌──────────────┐
         │ SPARSE SEARCH     │  │ DENSE SEARCH │  │ RRF FUSION   │
         │ (BM25)            │  │ (Vector)     │  │              │
         └───────────────────┘  └──────────────┘  └──────────────┘
                         │              │              │
                         └──────────────┴──────────────┘
                                        │
                                        ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP 1.1: Sparse Search (BM25)                       │
         │ - Index: anthropic-bm25-index                        │
         │ - Search fields: ["content", "contextualized_content"]│
         │ - Algorithm: BM25 (keyword matching)                 │
         │ - Returns: Top k*2 results with BM25 scores          │
         └──────────────────────────────────────────────────────┘
                                        │
                                        ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP 1.2: Dense Search (Vector)                      │
         │ - Embed query with Ollama BGE-M3                     │
         │ - Index: anthropic-vector-index                      │
         │ - Algorithm: KNN cosine similarity                   │
         │ - Returns: Top k*2 results with similarity scores    │
         └──────────────────────────────────────────────────────┘
                                        │
                                        ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP 1.3: RRF Fusion                                 │
         │ - Combine sparse + dense results                     │
         │ - Formula: score = 1 / (k + rank)                    │
         │ - k = 60 (RRF constant)                              │
         │ - Sort by fused score (descending)                   │
         │ - Return top k results                               │
         └──────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Format Results                                          │
│ For each result:                                                │
│   - doc_id: Document identifier                                 │
│   - score: RRF score                                            │
│   - source: {content, contextualized_content}                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT                                                           │
│ [1] Document doc_16 (RRF Score: 0.0167)                         │
│ Context: เมดไทยเป็นเว็บไซต์ที่ให้ข้อมูล...                      │
│ Content: # เมดไทย...                                            │
│                                                                  │
│ [2] Document doc_44 (RRF Score: 0.0167)                         │
│ Context: ...                                                     │
│ Content: ## อหิวาตกโรค...                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Code Path
```python
# main.py
async def search_documentation(query: str, limit: int = 5):
    results = rag_client.hybrid_search(query, k=limit)  # ← เรียก hybrid_search
    # Format results...
    return formatted_results

# authenticRAG.py
def hybrid_search(self, query, k=5, rrf_k=60):
    sparse_results = self.sparse_search(query, k=k*2)    # ← BM25
    dense_results = self.dense_search(query, k=k*2)      # ← Vector
    fused_results = self.rrf_fusion([sparse_results, dense_results], k=rrf_k)  # ← RRF
    return fused_results[:k]
```

### ไม่มีการใช้ LLM
- ❌ ไม่เรียก Qwen API
- ❌ ไม่สร้างคำตอบ
- ✅ แค่ค้นหาและจัดอันดับเอกสาร

---

## 💬 Tool 2: generate_answer

### Flow Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│ USER INPUT                                                       │
│ query: "อหิวาตกโรคคืออะไร"                                       │
│ use_context: true                                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ DECISION: use_context?                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼ (True)                        ▼ (False)
┌──────────────────────┐        ┌──────────────────────┐
│ WITH CONTEXT         │        │ WITHOUT CONTEXT      │
│ (RAG Pipeline)       │        │ (Direct LLM)         │
└──────────────────────┘        └──────────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ PATH A: WITH CONTEXT (use_context=True)                         │
│ Method: rag_client.search_for_question(query, k=5)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP A1: Hybrid Search (เหมือน search_documentation) │
         │ - Sparse search (BM25)                               │
         │ - Dense search (Vector)                              │
         │ - RRF fusion                                         │
         │ - Returns: Top 5 documents                           │
         └──────────────────────────────────────────────────────┘
                         │
                         ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP A2: Build Context                               │
         │ For each document:                                   │
         │   context += f"Content: {doc.content}\n"             │
         │   context += f"Context: {doc.contextualized_content}\n\n"│
         └──────────────────────────────────────────────────────┘
                         │
                         ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP A3: Truncate Context                            │
         │ - Max tokens: 4000                                   │
         │ - Estimate: words * 1.3 = tokens                     │
         │ - If too long: truncate and add "...(truncated)"     │
         └──────────────────────────────────────────────────────┘
                         │
                         ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP A4: Generate Response with LLM                  │
         │ Prompt:                                              │
         │   "You are a question answering assistant..."        │
         │   "Context information: {context}"                   │
         │   "Question: {question}"                             │
         │                                                      │
         │ LLM: Qwen 2.5-32B-Instruct                           │
         │ Temperature: 0.6                                     │
         │ Max tokens: 1000                                     │
         └──────────────────────────────────────────────────────┘
                         │
                         └──────────────┐
                                        │
┌─────────────────────────────────────────────────────────────────┐
│ PATH B: WITHOUT CONTEXT (use_context=False)                     │
│ Method: rag_client.call_qwen_api(query)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌──────────────────────────────────────────────────────┐
         │ STEP B1: Direct LLM Call                             │
         │ Prompt:                                              │
         │   "You are a question answering assistant..."        │
         │   "Question: {question}"                             │
         │                                                      │
         │ LLM: Qwen 2.5-32B-Instruct                           │
         │ Temperature: 0.2                                     │
         │ Max tokens: 500                                      │
         │                                                      │
         │ ⚠️ No context from documents!                        │
         └──────────────────────────────────────────────────────┘
                         │
                         └──────────────┐
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT (Natural Language Answer)                                │
│                                                                  │
│ อหิวาตกโรค หรือ โรคอหิวาต์, โรคอุจจาระร่วงอย่างแรง,            │
│ โรคลงราก หรือโรคห่า (Cholera) เป็นโรคอุจจาระร่วงเฉียบพลัน      │
│ ที่เกิดจากเชื้อแบคทีเรียชื่อ "วิบริโอคอเลอเร"                  │
│ (Vibrio cholerae)...                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Code Path
```python
# main.py
async def generate_answer(query: str, use_context: bool = True):
    if use_context:
        answer = rag_client.search_for_question(query, k=5)  # ← RAG pipeline
    else:
        answer = rag_client.call_qwen_api(query)             # ← Direct LLM
    return answer

# authenticRAG.py
def search_for_question(self, question, k=5):
    # 1. Search
    results = self.hybrid_search(question, k=k)  # ← เหมือน search_documentation
    
    # 2. Build context
    context = ""
    for doc_id, score, doc in results:
        content = doc.get("content", "")
        context_info = doc.get("contextualized_content", "")
        context += f"Content: {content}\nContext: {context_info}\n\n"
    
    # 3. Truncate if needed
    truncated_context = self.truncate_context(context, max_tokens=4000)
    
    # 4. Generate answer with LLM
    return self.generate_response(question, truncated_context)

def generate_response(self, question, context="", max_tokens=1000):
    prompt = f"""You are a question answering assistant...
    
Context information:
{context}

Question: {question}"""
    
    return self.call_qwen_api(prompt, max_tokens=max_tokens, temperature=0.6)
```

### ใช้ LLM (Qwen API)
- ✅ เรียก Qwen 2.5-32B-Instruct
- ✅ สร้างคำตอบเป็นภาษาธรรมชาติ
- ✅ ใช้ context จากเอกสารที่ค้นหาได้

---

## 🔄 ความเหมือนและต่าง

### ส่วนที่เหมือนกัน
1. **Hybrid Search** - ทั้ง 2 tools ใช้ `hybrid_search()` เหมือนกัน
   - BM25 (sparse search)
   - Vector similarity (dense search)
   - RRF fusion

2. **Data Source** - ค้นหาจาก OpenSearch indices เดียวกัน
   - `anthropic-bm25-index`
   - `anthropic-vector-index`

3. **Embedding Model** - ใช้ Ollama BGE-M3 เหมือนกัน

### ส่วนที่ต่างกัน

| Aspect | search_documentation | generate_answer |
|--------|---------------------|-----------------|
| **จบที่ไหน** | จบที่ search + format | ต่อไป generate answer |
| **LLM** | ไม่ใช้ | ใช้ Qwen API |
| **Output Type** | Structured (list of docs) | Unstructured (text) |
| **Context Building** | ไม่มี | มี (รวมเอกสาร 5 ชิ้น) |
| **Truncation** | ไม่มี | มี (max 4000 tokens) |
| **Temperature** | N/A | 0.6 (creative) |
| **Use Case** | ต้องการดูเอกสารต้นฉบับ | ต้องการคำตอบสรุป |

---

## 📈 Performance Comparison

### search_documentation
```
Speed: ⚡⚡⚡ Fast (no LLM)
Cost: 💰 Free (no API calls)
Accuracy: 📊 Depends on search quality
Control: 🎛️ High (user sees raw docs)
```

### generate_answer (use_context=True)
```
Speed: ⚡ Slower (LLM inference)
Cost: 💰💰 API cost per request
Accuracy: 📊📊 Higher (LLM reasoning)
Control: 🎛️ Low (LLM decides what to say)
```

### generate_answer (use_context=False)
```
Speed: ⚡ Slower (LLM inference)
Cost: 💰💰 API cost per request
Accuracy: 📊 Lower (no grounding)
Control: 🎛️ Very low (pure LLM knowledge)
```

---

## 🎯 Use Cases

### ใช้ search_documentation เมื่อ:
- ต้องการดูเอกสารต้นฉบับ
- ต้องการ score และ ranking
- ต้องการตรวจสอบความถูกต้อง
- ต้องการประหยัดค่า API
- ต้องการความเร็ว

**ตัวอย่าง:**
```
Query: "โรค"
→ ได้เอกสาร 3 ชิ้น พร้อม score
→ User อ่านเองและตัดสินใจ
```

### ใช้ generate_answer เมื่อ:
- ต้องการคำตอบโดยตรง
- ต้องการสรุปจากหลายเอกสาร
- ต้องการคำตอบเป็นภาษาธรรมชาติ
- User ไม่อยากอ่านเอกสารยาว
- ต้องการ reasoning จาก LLM

**ตัวอย่าง:**
```
Query: "อหิวาตกโรคคืออะไร"
→ ได้คำตอบสรุป 1 paragraph
→ User อ่านคำตอบเลย ไม่ต้องอ่านเอกสาร
```

---

## 🔧 Technical Details

### Hybrid Search Parameters
```python
# ใน hybrid_search()
k = 5              # จำนวนผลลัพธ์สุดท้าย
k*2 = 10           # ค้นหา sparse + dense ได้ 10 ชิ้นก่อน
rrf_k = 60         # RRF constant
```

### RRF Formula
```python
# สำหรับแต่ละเอกสาร
score = 0
for rank in [sparse_rank, dense_rank]:
    score += 1 / (60 + rank)

# เอกสารที่ติด top ทั้ง 2 วิธีจะได้ score สูง
```

### Context Truncation
```python
# ใน generate_answer
max_tokens = 4000
estimated_tokens = len(words) * 1.3

if estimated_tokens > max_tokens:
    target_words = int(max_tokens / 1.3)
    context = " ".join(words[:target_words]) + " ...(truncated)"
```

### LLM Settings
```python
# generate_answer (with context)
model = "qwen2.5-32b-instruct"
temperature = 0.6      # ค่อนข้าง creative
max_tokens = 1000      # คำตอบยาวได้

# generate_answer (without context)
temperature = 0.2      # เข้มงวดกว่า
max_tokens = 500       # คำตอบสั้นกว่า
```

---

## 📝 Summary

### search_documentation = Search Only
```
Input → Hybrid Search → Format → Output (Documents)
        ↓
        ├─ BM25 (keyword)
        ├─ Vector (semantic)
        └─ RRF (fusion)
```

### generate_answer = Search + Generate
```
Input → Hybrid Search → Build Context → Truncate → LLM → Output (Answer)
        ↓               ↓                ↓          ↓
        (same as        Combine 5        Max 4000   Qwen API
         above)         documents        tokens     (reasoning)
```

**Key Difference:**
- `search_documentation` = **Retrieval** only
- `generate_answer` = **Retrieval + Generation** (RAG)

---

## 🎓 Analogy

### search_documentation
```
เหมือนการถาม librarian:
"หาหนังสือเกี่ยวกับโรคให้หน่อย"

→ Librarian หาหนังสือ 3 เล่มมาให้
→ คุณต้องอ่านเอง
```

### generate_answer
```
เหมือนการถาม expert:
"อหิวาตกโรคคืออะไร"

→ Expert หาหนังสือ 5 เล่ม (ภายใน)
→ Expert อ่านและสรุปให้คุณฟัง
→ คุณได้คำตอบเลย ไม่ต้องอ่านเอง
```
