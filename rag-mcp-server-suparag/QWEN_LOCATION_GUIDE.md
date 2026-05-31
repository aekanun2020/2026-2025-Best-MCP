# Qwen 2.5-32B อยู่ที่ไหนในโค้ด

## 📍 ตำแหน่งหลัก

Qwen 2.5-32B อยู่ใน **`authenticRAG.py`** ที่ method `call_qwen_api()`

**ไฟล์:** `2026-ContextualRAG-MCP-Streamable-HTTP/AuthenticRAG-Qwen2.5API/authenticRAG.py`

---

## 🔧 Configuration

### 1. Initialization (บรรทัด 20-30)
```python
class AnthropicStyleContextualRAG:
    def __init__(self, opensearch_host="localhost", opensearch_port=9200, ollama_url="http://localhost:11434"):
        # รับ API key จาก environment variable
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set")
        
        # สร้าง OpenAI client ที่ใช้เรียก Qwen API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"  # ← Qwen API endpoint
        )
```

**สิ่งที่ต้องมี:**
- `DASHSCOPE_API_KEY` environment variable
- OpenAI Python library (ใช้เป็น client)
- Base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

---

### 2. API Call Method (บรรทัด 132-145)
```python
def call_qwen_api(self, prompt, max_tokens=500, temperature=0.2):
    """เรียกใช้ Qwen API เพื่อสร้างข้อความ"""
    try:
        completion = self.client.chat.completions.create(
            model="qwen2.5-32b-instruct",  # ← โมเดลที่ใช้
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling Qwen API: {e}")
        return f"Qwen API error: {str(e)}"
```

**Parameters:**
- `model`: `"qwen2.5-32b-instruct"` ← **ตรงนี้คือที่กำหนดโมเดล**
- `max_tokens`: จำนวน tokens สูงสุดที่ตอบได้
- `temperature`: ความ creative (0.0-1.0)

---

## 🎯 ใช้งานที่ไหนบ้าง

### 1. Generate Context (บรรทัด 165-169)
```python
def generate_context(self, document_content, chunk_content):
    """สร้างบริบทโดยใช้ Qwen API"""
    prompt = self.get_context_prompt(document_content, chunk_content)
    context = self.call_qwen_api(prompt, max_tokens=100, temperature=0.1)  # ← ใช้ที่นี่
    return context.strip()
```

**จุดประสงค์:** สร้าง contextualized content สำหรับแต่ละ chunk  
**เรียกเมื่อ:** `add_documents_with_context()` - ตอน indexing เอกสาร  
**Settings:**
- `max_tokens=100` (สั้น เพราะแค่สร้าง context)
- `temperature=0.1` (เข้มงวด ต้องการความแม่นยำ)

---

### 2. Generate Response (บรรทัด 285-300)
```python
def generate_response(self, question, context="", max_tokens=1000):
    """สร้างคำตอบจากคำถามและ context"""
    if not context:
        prompt = f"""You are a question answering assistant. Answer the question as truthful and helpful as possible.

Question: {question}"""
    else:
        prompt = f"""You are a question answering assistant. Answer the question as truthful and helpful as possible.

Context information:
{context}

Question: {question}"""

    return self.call_qwen_api(prompt, max_tokens=max_tokens, temperature=0.6)  # ← ใช้ที่นี่
```

**จุดประสงค์:** สร้างคำตอบจากคำถาม (พร้อม context หรือไม่มีก็ได้)  
**เรียกเมื่อ:** `search_for_question()` - ตอนตอบคำถาม  
**Settings:**
- `max_tokens=1000` (ยาว เพราะต้องตอบคำถาม)
- `temperature=0.6` (ค่อนข้าง creative เพื่อให้คำตอบหลากหลาย)

---

## 🔄 Call Flow

### Flow 1: Indexing Documents (ใช้ Qwen สร้าง context)
```
add_documents_with_context()
    ↓
    For each chunk:
        ↓
        generate_context(full_doc, chunk)
            ↓
            get_context_prompt()  → สร้าง prompt
            ↓
            call_qwen_api(prompt, max_tokens=100, temperature=0.1)  ← Qwen ทำงาน
                ↓
                model="qwen2.5-32b-instruct"
                ↓
                Return: contextualized content
```

**ตัวอย่าง Prompt:**
```
<document>
{full document content}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk content}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval. Answer only with the succinct context and nothing else.
```

**ตัวอย่าง Output:**
```
เมดไทยเป็นเว็บไซต์ที่ให้ข้อมูลเกี่ยวกับการดูแลสุขภาพและการรักษาโรค
```

---

### Flow 2: Answering Questions (ใช้ Qwen สร้างคำตอบ)
```
search_for_question(question)
    ↓
    hybrid_search(question)  → ค้นหาเอกสาร 5 ชิ้น
    ↓
    Build context from 5 documents
    ↓
    truncate_context(context, max_tokens=4000)
    ↓
    generate_response(question, context, max_tokens=1000)
        ↓
        call_qwen_api(prompt, max_tokens=1000, temperature=0.6)  ← Qwen ทำงาน
            ↓
            model="qwen2.5-32b-instruct"
            ↓
            Return: natural language answer
```

**ตัวอย่าง Prompt:**
```
You are a question answering assistant. Answer the question as truthful and helpful as possible.

Context information:
Content: อหิวาตกโรค (Cholera) เป็นโรคอุจจาระร่วงเฉียบพลัน...
Context: โรคที่เกิดจากเชื้อแบคทีเรีย Vibrio cholerae...

Content: อาการของโรคอหิวาตกโรค...
Context: อาการหลักคือท้องร่วงเป็นน้ำและอาเจียน...

Question: อหิวาตกโรคคืออะไร
```

**ตัวอย่าง Output:**
```
อหิวาตกโรค หรือ โรคอหิวาต์, โรคอุจจาระร่วงอย่างแรง, โรคลงราก หรือโรคห่า (Cholera) 
เป็นโรคอุจจาระร่วงเฉียบพลันที่เกิดจากเชื้อแบคทีเรียชื่อ "วิบริโอคอเลอเร" (Vibrio cholerae)...
```

---

## 🌐 API Endpoint

### Qwen API (Alibaba Cloud)
```
Base URL: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
Model: qwen2.5-32b-instruct
API Key: DASHSCOPE_API_KEY (from .env)
```

**ไม่ใช่ Ollama!**
- Qwen 2.5-32B รันบน **Alibaba Cloud** (remote API)
- Ollama รันแค่ **BGE-M3** (embedding model) บน local container

---

## 📊 Model Comparison

| Model | Purpose | Location | API |
|-------|---------|----------|-----|
| **Qwen 2.5-32B** | Text generation (LLM) | Alibaba Cloud | DASHSCOPE_API_KEY |
| **BGE-M3** | Embeddings (1024-dim) | Ollama container | http://ollama:11434 |
| **Qwen 2.5:14B** | ❌ ไม่ได้ใช้ | Ollama container | - |
| **nomic-embed-text** | ❌ ไม่ได้ใช้ | Ollama container | - |

---

## 🔑 Environment Variables

### ใน `.env` file
```bash
# Qwen API (Alibaba Cloud)
DASHSCOPE_API_KEY=sk-REDACTED_SET_VIA_ENV

# Ollama (Local)
OLLAMA_URL=http://ollama:11434
```

### ใน `docker-compose.yml`
```yaml
mcp-server:
  environment:
    - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}  # ← Qwen API key
    - OLLAMA_URL=http://ollama:11434           # ← Ollama URL
```

---

## 🎛️ Temperature Settings

| Use Case | Temperature | Reason |
|----------|-------------|--------|
| **Generate Context** | 0.1 | ต้องการความแม่นยำสูง, ไม่ต้องการความ creative |
| **Answer Question** | 0.6 | ต้องการคำตอบที่หลากหลาย, อ่านง่าย |
| **Direct Answer (no context)** | 0.2 | เข้มงวดกว่า เพราะไม่มี context ช่วย |

**Temperature Scale:**
- `0.0` = Deterministic (เลือกคำที่มี probability สูงสุดเสมอ)
- `0.5` = Balanced
- `1.0` = Very creative (สุ่มมาก)

---

## 📝 Summary

### Qwen 2.5-32B อยู่ที่:
```python
# File: authenticRAG.py
# Line: 135

def call_qwen_api(self, prompt, max_tokens=500, temperature=0.2):
    completion = self.client.chat.completions.create(
        model="qwen2.5-32b-instruct",  # ← ตรงนี้!
        messages=[...],
        max_tokens=max_tokens,
        temperature=temperature
    )
```

### ใช้งาน 2 จุด:
1. **Generate Context** (ตอน indexing)
   - `generate_context()` → `call_qwen_api(max_tokens=100, temperature=0.1)`
   
2. **Generate Answer** (ตอนตอบคำถาม)
   - `generate_response()` → `call_qwen_api(max_tokens=1000, temperature=0.6)`

### API Configuration:
- **Endpoint:** Alibaba Cloud DashScope
- **API Key:** `DASHSCOPE_API_KEY` from `.env`
- **Model:** `qwen2.5-32b-instruct`
- **Client:** OpenAI Python library (compatible mode)

---

## 🔧 ถ้าอยากเปลี่ยนโมเดล

### เปลี่ยนเป็น Qwen 2.5-72B
```python
# Line 135 in authenticRAG.py
model="qwen2.5-72b-instruct",  # ← เปลี่ยนตรงนี้
```

### เปลี่ยนเป็น Ollama Qwen 2.5:14B (local)
```python
def call_qwen_api(self, prompt, max_tokens=500, temperature=0.2):
    response = requests.post(
        f"{self.ollama_url}/api/generate",
        json={
            "model": "qwen2.5:14b",
            "prompt": prompt,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
    )
    return response.json()["response"]
```

**แต่ต้องแก้ทั้ง 2 จุด:**
1. `generate_context()`
2. `generate_response()`
