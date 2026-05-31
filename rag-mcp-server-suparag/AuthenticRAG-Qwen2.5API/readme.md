# คู่มือการติดตั้งและใช้งานระบบ RAG ขั้นสูง

คู่มือนี้ให้คำแนะนำขั้นตอนต่อขั้นตอนสำหรับการติดตั้งและใช้งานระบบ RAG (Retrieval-Augmented Generation) ขั้นสูงด้วย OpenSearch, Ollama และ Python

## เริ่มต้นอย่างรวดเร็ว (Quick Start)

```bash
# 1. ติดตั้ง dependencies
pip install opensearchpy sentence-transformers llama-index llama-index-embeddings-huggingface openai tqdm

# 2. ติดตั้ง Docker และเปิด OpenSearch
docker network create opensearch-net
docker run -e OPENSEARCH_JAVA_OPTS="-Xms512m -Xmx512m" -e discovery.type="single-node" \
  -e DISABLE_SECURITY_PLUGIN="true" -e bootstrap.memory_lock="true" \
  -e cluster.name="opensearch-cluster" -e node.name="os01" \
  -e plugins.neural_search.hybrid_search_disabled="true" \
  -e DISABLE_INSTALL_DEMO_CONFIG="true" \
  --ulimit nofile="65536:65536" --ulimit memlock="-1:-1" \
  --net opensearch-net --restart=no \
  -v opensearch-data:/usr/share/opensearch/data \
  -p 9200:9200 \
  --name=opensearch-single-node \
  opensearchproject/opensearch:latest

# 3. ตั้งค่า Hybrid Search Pipeline
curl -XPUT "http://localhost:9200/_search/pipeline/hybrid-search-pipeline" -H "Content-Type: application/json" -d'{"description": "Pipeline for hybrid search","phase_results_processors": [{"normalization-processor": {"normalization": {"technique": "min_max"},"combination": {"technique": "harmonic_mean","parameters": {"weights": [0.3,0.7]}}}}]}'

# 4. ตั้งค่า API Key สำหรับ DashScope (Qwen API)
export DASHSCOPE_API_KEY='your_api_key_here'

# 5. รันโค้ดสร้าง RAG System
python authenticRAG.py
```

## ความต้องการของระบบ

- Python 3.10+
- Docker Desktop
- RAM 8GB+ (แนะนำ)
- API Key สำหรับ DashScope (Qwen API)

## คู่มือการติดตั้งโดยละเอียด

### 1. การเตรียมสภาพแวดล้อม

#### ทางเลือกที่ 1: ใช้ Conda (แนะนำ)

```bash
# สร้างสภาพแวดล้อมใหม่ด้วย Conda
conda create -n advrag python=3.10
conda activate advrag

# ติดตั้ง dependencies
pip install opensearch-py sentence-transformers llama-index llama-index-embeddings-huggingface openai tqdm
```

#### ทางเลือกที่ 2: ใช้ venv

```bash
# สร้างสภาพแวดล้อมเสมือน
python -m venv venv

# เปิดใช้งานสภาพแวดล้อมเสมือน
# สำหรับ Windows
venv\Scripts\activate
# สำหรับ macOS/Linux
source venv/bin/activate

# ติดตั้ง dependencies
pip install opensearch-py sentence-transformers llama-index llama-index-embeddings-huggingface openai tqdm
```

### 2. ติดตั้ง Docker และตั้งค่า OpenSearch

#### การติดตั้ง Docker Desktop

1. ดาวน์โหลดและติดตั้ง Docker Desktop จาก [เว็บไซต์อย่างเป็นทางการ](https://www.docker.com/products/docker-desktop/)
2. เปิด Docker Desktop และรอให้เริ่มต้นทำงาน

#### รัน OpenSearch Container

สร้างเครือข่าย Docker แบบกำหนดเองเพื่อให้คอนเทนเนอร์สามารถสื่อสารกันได้อย่างปลอดภัย:

```bash
docker network create opensearch-net
```

##### สำหรับ Linux/macOS:

```bash
docker run -e OPENSEARCH_JAVA_OPTS="-Xms512m -Xmx512m" -e discovery.type="single-node" \
  -e DISABLE_SECURITY_PLUGIN="true" -e bootstrap.memory_lock="true" \
  -e cluster.name="opensearch-cluster" -e node.name="os01" \
  -e plugins.neural_search.hybrid_search_disabled="true" \
  -e DISABLE_INSTALL_DEMO_CONFIG="true" \
  --ulimit nofile="65536:65536" --ulimit memlock="-1:-1" \
  --net opensearch-net --restart=no \
  -v opensearch-data:/usr/share/opensearch/data \
  -p 9200:9200 \
  --name=opensearch-single-node \
  opensearchproject/opensearch:latest
```

##### สำหรับ Windows PowerShell:

```powershell
docker run -e OPENSEARCH_JAVA_OPTS="-Xms512m -Xmx512m" -e discovery.type="single-node" `
  -e DISABLE_SECURITY_PLUGIN="true" -e bootstrap.memory_lock="true" `
  -e cluster.name="opensearch-cluster" -e node.name="os01" `
  -e plugins.neural_search.hybrid_search_disabled="true" `
  -e DISABLE_INSTALL_DEMO_CONFIG="true" `
  --ulimit nofile="65536:65536" --ulimit memlock="-1:-1" `
  --net opensearch-net --restart=no `
  -v opensearch-data:/usr/share/opensearch/data `
  -p 9200:9200 `
  --name=opensearch-single-node `
  opensearchproject/opensearch:latest
```

##### สำหรับ Command Prompt:

```bash
docker run -e OPENSEARCH_JAVA_OPTS="-Xms512m -Xmx512m" -e discovery.type="single-node" -e DISABLE_SECURITY_PLUGIN="true" -e bootstrap.memory_lock="true" -e cluster.name="opensearch-cluster" -e node.name="os01" -e plugins.neural_search.hybrid_search_disabled="true" -e DISABLE_INSTALL_DEMO_CONFIG="true" --ulimit nofile="65536:65536" --ulimit memlock="-1:-1" --net opensearch-net --restart=no -v opensearch-data:/usr/share/opensearch/data -p 9200:9200 --name=opensearch-single-node opensearchproject/opensearch:latest
```

### 3. ตั้งค่า Hybrid Search Pipeline

ขั้นตอนนี้ตั้งค่าไปป์ไลน์การค้นหาแบบไฮบริดที่ผสมผสานระหว่างการค้นหาแบบใช้คีย์เวิร์ดและการค้นหาเชิงความหมาย

#### สำหรับ Linux/macOS:

```bash
curl -XPUT "http://localhost:9200/_search/pipeline/hybrid-search-pipeline" \
  -H "Content-Type: application/json" \
  -d'{"description": "Pipeline for hybrid search","phase_results_processors": [{"normalization-processor": {"normalization": {"technique": "min_max"},"combination": {"technique": "harmonic_mean","parameters": {"weights": [0.3,0.7]}}}}]}'
```

#### สำหรับ Windows (PowerShell):

```powershell
Invoke-WebRequest -Method PUT -Uri "http://localhost:9200/_search/pipeline/hybrid-search-pipeline" -Headers @{"Content-Type"="application/json"} -Body @"
{
  "description": "Pipeline for hybrid search",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": {
          "technique": "min_max"
        },
        "combination": {
          "technique": "harmonic_mean",
          "parameters": {
            "weights": [
              0.3,
              0.7
            ]
          }
        }
      }
    }
  ]
}
"@
```

### 4. ตั้งค่า API Key สำหรับ DashScope (Qwen API)

ระบบใช้ DashScope API (Qwen model) สำหรับการสร้างบริบทและตอบคำถาม คุณต้องตั้งค่า API key เป็นตัวแปรสภาพแวดล้อม:

```bash
# Linux/macOS
export DASHSCOPE_API_KEY='your_api_key_here'

# Windows (Command Prompt)
set DASHSCOPE_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:DASHSCOPE_API_KEY='your_api_key_here'
```

### 5. การดาวน์โหลดคอร์ปัส (Corpus) สำหรับทดสอบ

ระบบสามารถดาวน์โหลดคอร์ปัสตัวอย่างได้อัตโนมัติ หรือคุณสามารถใช้เอกสารของคุณเองโดยวางไว้ในโฟลเดอร์ `corpus_input` (ต้องสร้างโฟลเดอร์นี้ถ้ายังไม่มี)

## การใช้งานระบบ

### 1. ใช้งาน AnthropicStyleContextualRAG

หลักการทำงานของสคริปต์ authenticRAG.py:

```python
# ตัวอย่างโค้ดการใช้งานระบบ
from authenticRAG import AnthropicStyleContextualRAG

# ตั้งค่าระบบ
rag = AnthropicStyleContextualRAG(
    opensearch_host="34.41.37.53",  # IP ของ OpenSearch ตามที่ระบุในโค้ด
    opensearch_port=9200
)

# โหลดเอกสาร
md_paths = [
    "./corpus_input/1.md",
    "./corpus_input/2.md",
    "./corpus_input/44.md",
    "./corpus_input/5555.md"
]
docs = rag.load_documents(md_paths)

# เพิ่มเอกสารเข้า OpenSearch พร้อมสร้างบริบท
rag.add_documents_with_context(docs)

# ค้นหาและตอบคำถาม
question = "ผมมีไข้และมีผื่นเป็นจุดแดงเล็กๆ ผมเป็นโรคอะไร"
answer = rag.search_for_question(question)
print(f"คำตอบ: {answer}")
```

### 2. ใช้งาน AuthenticSearchRAG

หลักการทำงานของสคริปต์ onlysearchAuthenticRAG.py:

```python
# ตัวอย่างโค้ดการใช้งานระบบค้นหา
from onlysearchAuthenticRAG import AuthenticSearchRAG

# ตั้งค่าระบบ
rag = AuthenticSearchRAG(
    opensearch_host="34.41.37.53",  # IP ของ OpenSearch ตามที่ระบุในโค้ด
    opensearch_port=9200
)

# ชุดคำถามที่ต้องการค้นหา
questions = [
    "Congenital Rubella Syndrome คืออะไร",
    "ผื่นจากโรคหัดเยอรมันมีลักษณะอย่างไร",
    "10 วิธีการรักษาโรคหัดเยอรมัน",
    "วัคซีนป้องกันโรคหัดเยอรมันฉีดเมื่อไหร่?"
]

# ค้นหาและตอบคำถาม
results = rag.search_multiple_questions(questions, k=5)

# ส่งออกผลลัพธ์ไปยังไฟล์ JSON
rag.export_results_to_json(results, "authentic_rag_search_results.json")
```

### 3. การรันสคริปต์

รันไฟล์ authenticRAG.py สำหรับการเตรียมและทดสอบระบบหลัก:

```bash
# รันสคริปต์หลัก
python authenticRAG.py
```

สำหรับการค้นหาและตอบคำถามโดยเฉพาะ:

```bash
# รันสคริปต์ค้นหา
python onlysearchAuthenticRAG.py
```

## โครงสร้างโฟลเดอร์

```
project_root/
├── corpus_input/          # โฟลเดอร์สำหรับเก็บไฟล์ Markdown
├── authenticRAG.py        # โค้ดหลักสำหรับ AuthenticRAG
├── onlysearchAuthenticRAG.py  # สคริปต์สำหรับการค้นหาโดยใช้ AuthenticRAG
└── authentic_rag_search_results.json # ไฟล์ผลลัพธ์จากการค้นหา
```

## การแก้ไขปัญหา

### ปัญหาการเชื่อมต่อกับ OpenSearch

```bash
# ตรวจสอบว่า OpenSearch กำลังทำงานอยู่
curl http://localhost:9200

# เอาต์พุตที่คาดหวังควรมีข้อมูลเวอร์ชันของ OpenSearch
```

### ตรวจสอบสถานะ Docker

```bash
# ตรวจสอบสถานะคอนเทนเนอร์ Docker
docker ps -a | grep opensearch

# รีสตาร์ท OpenSearch หากจำเป็น
docker restart opensearch-single-node
```

### ปัญหาทั่วไปเกี่ยวกับ Python

- หากพบข้อผิดพลาดการนำเข้าโมดูล ตรวจสอบให้แน่ใจว่าสภาพแวดล้อมเสมือนของคุณเปิดใช้งานอยู่
- สำหรับข้อผิดพลาดที่เกี่ยวข้องกับ API Key ตรวจสอบให้แน่ใจว่าคุณได้ตั้งค่าตัวแปรสภาพแวดล้อม DASHSCOPE_API_KEY แล้ว

## การปรับแต่งเพิ่มเติม

### การใช้โมเดล Embedding อื่น

ระบบใช้โมเดล BAAI/bge-m3 เป็นค่าเริ่มต้น หากต้องการเปลี่ยนโมเดล ให้แก้ไขในโค้ด:

```python
# เปลี่ยนจาก
self.embed_model = SentenceTransformer('BAAI/bge-m3')

# เป็นโมเดลอื่น เช่น
self.embed_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
```

### การปรับค่าพารามิเตอร์ในการค้นหา

- `k`: จำนวนเอกสารที่จะดึงมา (ค่าเริ่มต้นคือ 5)
- `rrf_k`: ค่าพารามิเตอร์สำหรับ Reciprocal Rank Fusion (ค่าเริ่มต้นคือ 60)

```python
# ปรับพารามิเตอร์ในการค้นหา
results = rag.hybrid_search(question, k=10, rrf_k=40)
```

## ข้อมูลเพิ่มเติม

สำหรับข้อมูลโดยละเอียดเกี่ยวกับตัวเลือกการกำหนดค่าและการใช้งานขั้นสูง โปรดดูเอกสารประกอบของไลบรารีที่ใช้:

- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [sentence-transformers Documentation](https://www.sbert.net/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
