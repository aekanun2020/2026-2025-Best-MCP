# 2026 ContextualRAG - Developer Documentation

## 📍 Project Location

```bash
# Local Path
/Users/grizzlymacbookpro/2025-Dev-AnthropicContextualRAG-main

# Quick Access
cd ~/2025-Dev-AnthropicContextualRAG-main
cd AuthenticRAG-Qwen2.5API  # Main project folder

# GitHub Repository
https://github.com/aekanun2020/2026-ContextualRAG.git
```

---

## 📋 Overview

ระบบ Retrieval-Augmented Generation (RAG) ที่ใช้เทคนิค Contextual Retrieval จาก Anthropic ร่วมกับ Hybrid Search (BM25 + Vector Search + RRF) เพื่อปรับปรุงความแม่นยำในการค้นหาและตอบคำถาม

---

## ⭐ Stable Version (Most Reliable)

**Version:** 1.0.0 (Command Line)  
**Commit:** `c2728ed` - Initial commit: AuthenticRAG v1.0.0  
**Date:** March 7, 2026

นี่คือ version ที่น่าเชื่อถือที่สุด เพราะผ่านการทดสอบอย่างหนักด้วย 15 คำถามที่ท้าทาย

**ผลการทดสอบ:**
- 📊 [Test Results](AuthenticRAG-Qwen2.5API/advanced_test_results.json) - ผลการทดสอบ 15 คำถาม
- ✅ ทดสอบครบทุกคำถาม พร้อมคำตอบและแหล่งอ้างอิง
- 🎯 Command line version ที่ stable และพร้อมใช้งาน

**ไฟล์หลัก:**
- `onlysearchAuthenticRAG.py` - Search และตอบคำถาม (แนะนำ)
- `test_advanced_questions.py` - ชุดทดสอบ 15 คำถาม
- `advanced_test_results.json` - ผลการทดสอบ

**Checkout stable version:**
```bash
git checkout c2728ed
```

---

## 🏗️ Architecture

### Core Components

1. **Contextual Embedding**
   - ใช้ Qwen API สร้าง context สำหรับแต่ละ chunk
   - เพิ่มความเข้าใจบริบทของเอกสาร
   - ลด hallucination และเพิ่มความแม่นยำ

2. **Hybrid Search**
   - **BM25**: Keyword-based search (Lexical)
   - **Vector Search**: Semantic search using BAAI/bge-m3
   - **RRF (Reciprocal Rank Fusion)**: รวมผลลัพธ์จาก 2 วิธี

3. **OpenSearch**
   - เก็บ embeddings และ metadata
   - รองรับ hybrid search
   - Index: `contextual_chunks`

4. **Answer Generation**
   - ใช้ Qwen API สร้างคำตอบจาก retrieved documents
   - รองรับภาษาไทย

## 📁 Project Structure

```
AuthenticRAG-Qwen2.5API/
├── authenticRAG.py                    # Main script (full pipeline)
├── onlysearchAuthenticRAG.py          # Search-only script
├── onlysearchAuthenticRAG-moredocsAnswer.py  # Multiple questions
├── test_advanced_questions.py         # Advanced test suite
├── demo_check_system.py               # System verification
├── api_server.py                      # FastAPI backend server
├── streamlit_app.py                   # Streamlit web UI
├── start_ui.sh                        # UI startup script
├── requirements.txt                   # Python dependencies
├── requirements-ui.txt                # UI dependencies
├── setup.sh                          # Setup script
├── QUICKSTART.md                     # Quick start guide
├── UI-GUIDE.md                       # UI user guide
├── corpus_input/                     # Input documents (Markdown)
│   ├── 1.md                         # โรคหัดเยอรมัน
│   ├── 2.md                         # อหิวาตกโรค
│   ├── 44.md                        # ต้อกระจก
│   └── 5555.md                      # กรดไหลย้อน
├── backup/                           # Backup files
├── evaluation_summary.md             # Test evaluation template
└── advanced_test_results.json        # Test results
```

---

## 🐳 Docker Volume Mappings

### Container Architecture

The system uses 4 Docker containers with specific volume mappings:

#### 1. MCP Server (contextual-rag-mcp)
```yaml
volumes:
  - ./AuthenticRAG-Qwen2.5API:/app/rag:ro  # Read-only access
```

**Mapping:**
- Host: `./AuthenticRAG-Qwen2.5API`
- Container: `/app/rag`
- Mode: Read-Only (ro)
- Purpose: Access to authenticRAG.py and corpus_input for indexing

#### 2. Streamlit UI (contextual-rag-ui)
```yaml
volumes:
  - ./AuthenticRAG-Qwen2.5API:/app          # Read-write access
  - ./AuthenticRAG-Qwen2.5API/corpus_input:/app/corpus_input  # Explicit mapping
```

**Mapping:**
- Host: `./AuthenticRAG-Qwen2.5API`
- Container: `/app`
- Mode: Read-Write (rw)
- Purpose: Full access for document management (add/edit/delete)

**Document Storage:**
- Host: `./AuthenticRAG-Qwen2.5API/corpus_input/`
- Container: `/app/corpus_input/`
- Shared between: MCP Server (read-only) and Streamlit UI (read-write)

#### 3. OpenSearch (contextual-rag-opensearch)
```yaml
volumes:
  - opensearch-data:/usr/share/opensearch/data
```

**Mapping:**
- Type: Named Volume (Docker-managed)
- Container: `/usr/share/opensearch/data`
- Purpose: Persistent storage for indices

#### 4. Ollama (contextual-rag-ollama)
```yaml
volumes:
  - ollama-data:/root/.ollama
  - ./ollama-entrypoint.sh:/entrypoint.sh:ro
```

**Mapping:**
- Type: Named Volume + Bind Mount
- Container: `/root/.ollama` (models), `/entrypoint.sh` (script)
- Purpose: Model storage and startup script

### Document Flow

```
User uploads file via Streamlit UI
    ↓
Saved to /app/corpus_input/ (in streamlit container)
    ↓
Synced to host: ./AuthenticRAG-Qwen2.5API/corpus_input/
    ↓
Visible to MCP Server: /app/rag/corpus_input/ (read-only)
    ↓
Index to OpenSearch → stored in opensearch-data volume
```

### Important Notes

1. **corpus_input/** is the shared directory between containers
2. **Streamlit UI** can add/edit/delete files (read-write)
3. **MCP Server** can only read files for indexing (read-only)
4. **Changes sync bidirectionally** between host and containers
5. **Named volumes** (opensearch-data, ollama-data) persist across container restarts

### Accessing Files

```bash
# List files in Streamlit container
docker exec contextual-rag-ui ls -la /app/corpus_input/

# List files in MCP Server container
docker exec contextual-rag-mcp ls -la /app/rag/corpus_input/

# List files on host
ls -la AuthenticRAG-Qwen2.5API/corpus_input/

# All three should show the same files
```

**See [VOLUME_MAPPING_GUIDE.md](VOLUME_MAPPING_GUIDE.md) for complete details.**

## 🔧 Technical Details

### Dependencies

```bash
# Core
opensearch-py==2.7.1
sentence-transformers==3.2.1
requests==2.32.3

# Optional (for full pipeline)
llama-index==0.12.5
langchain==0.3.7
```

### OpenSearch Configuration

```python
# Connection
host = 'localhost'
port = 9200
index_name = 'contextual_chunks'

# Index Settings
{
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "chunk_id": {"type": "keyword"},
            "original_chunk": {"type": "text"},
            "contextualized_chunk": {"type": "text"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib"
                }
            },
            "doc_id": {"type": "keyword"},
            "context": {"type": "text"}
        }
    }
}
```

### Embedding Model

```python
model_name = "BAAI/bge-m3"
dimension = 1024
```

### Qwen API

```python
api_url = "https://api.aiforthai.in.th/v3/qwen-max"
headers = {
    "Apikey": "YOUR_API_KEY",
    "Content-Type": "application/json"
}
```

## 🚀 Development Workflow

### 1. Setup Environment

```bash
cd AuthenticRAG-Qwen2.5API
chmod +x setup.sh
./setup.sh
```

### 2. Verify System

```bash
python demo_check_system.py
```

### 3. Index Documents (Full Pipeline)

```bash
python authenticRAG.py
```

**Process:**
1. Read Markdown files from `corpus_input/`
2. Split into chunks (500 chars, overlap 50)
3. Generate context using Qwen API
4. Create embeddings using bge-m3
5. Store in OpenSearch

### 4. Search Only

```bash
python onlysearchAuthenticRAG.py
```

**Features:**
- Hybrid search (BM25 + Vector)
- RRF fusion
- Answer generation
- Save results to JSON

### 5. Run Tests

```bash
python test_advanced_questions.py
```

**Test Categories:**
- Cross-disease comparison
- Mechanism-based questions
- Rare complications
- Statistical questions
- Treatment-specific questions
- Analytical reasoning

### 6. Start Web UI (NEW)

```bash
# Quick start (recommended)
./start_ui.sh

# Or start manually
# Terminal 1: FastAPI Backend
python api_server.py

# Terminal 2: Streamlit Frontend
streamlit run streamlit_app.py
```

**UI Features:**
- 🎨 Web interface for search and Q&A
- 📊 Real-time system monitoring
- 🔍 Hybrid search with adjustable weights
- 💡 Answer generation with sources
- 📜 Search history tracking

**URLs:**
- Streamlit UI: http://localhost:8501
- FastAPI Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

**See [UI-GUIDE.md](AuthenticRAG-Qwen2.5API/UI-GUIDE.md) for detailed usage**

## 📊 Performance Metrics

### Search Performance

```python
# Hybrid Search Parameters
sparse_weight = 0.5  # BM25 weight
dense_weight = 0.5   # Vector weight
k = 60              # RRF constant
top_k = 10          # Results per search
final_top_k = 5     # Final results
```

### Current Stats

- **Documents Indexed**: 53 chunks
- **Average Query Time**: ~2-3 seconds
- **Embedding Dimension**: 1024
- **Context Window**: 500 characters

## 🧪 Testing

### Test Suite Structure

```python
questions = [
    {
        "question": "คำถามทดสอบ",
        "category": "หมวดหมู่",
        "difficulty": "ระดับความยาก"
    }
]
```

### Evaluation Criteria

1. **ตอบถูกแต่ไม่ครบ** - ข้อมูลถูกต้องแต่ขาดรายละเอียด
2. **ตอบถูกและครบถ้วน** - ข้อมูลถูกต้องและครอบคลุม
3. **ตอบไม่ถูก** - ข้อมูลผิดหรือไม่ตรงคำถาม

## 🔍 Debugging

### Check OpenSearch

```bash
# Check cluster health
curl -X GET "localhost:9200/_cluster/health?pretty"

# Check index
curl -X GET "localhost:9200/contextual_chunks/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match_all": {}}, "size": 1}'

# Count documents
curl -X GET "localhost:9200/contextual_chunks/_count?pretty"
```

### Common Issues

1. **OpenSearch not running**
   ```bash
   # Check status
   curl -X GET "localhost:9200"
   ```

2. **API Key issues**
   - Verify API key in script
   - Check API quota/limits

3. **Embedding errors**
   - Check model download
   - Verify CUDA/CPU compatibility

## 📝 Code Examples

### Custom Search

```python
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer

# Initialize
client = OpenSearch([{'host': 'localhost', 'port': 9200}])
model = SentenceTransformer('BAAI/bge-m3')

# Search
query = "คำถามของคุณ"
query_embedding = model.encode(query).tolist()

response = client.search(
    index='contextual_chunks',
    body={
        "query": {
            "hybrid": {
                "queries": [
                    {"match": {"contextualized_chunk": query}},
                    {"knn": {"embedding": {"vector": query_embedding, "k": 10}}}
                ]
            }
        },
        "size": 5
    }
)
```

### Custom Context Generation

```python
import requests

def generate_context(chunk, doc_content):
    prompt = f"""<document>
{doc_content}
</document>

สร้างบริบทสั้นๆ สำหรับข้อความนี้:
{chunk}

บริบท:"""
    
    response = requests.post(
        "https://api.aiforthai.in.th/v3/qwen-max",
        headers={"Apikey": "YOUR_KEY", "Content-Type": "application/json"},
        json={"model": "qwen-max", "messages": [{"role": "user", "content": prompt}]}
    )
    
    return response.json()['choices'][0]['message']['content']
```

## 🔐 Security Notes

- API keys should be stored in environment variables
- Never commit API keys to version control
- Use `.gitignore` for sensitive files

## 🔄 Migration Guide

### From Legacy Version (Root Level) to Current Version

#### What Changed?

**Old Structure (Deprecated - July 2025):**
```
root/
├── authenticRAG.py                    # Old implementation
├── OpenSearch-Reader-Without-Truncation-ALLdocs.py
└── result-withChallenge-from-GPT4
```

**New Structure (Current - August 2025 → Present):**
```
AuthenticRAG-Qwen2.5API/
├── authenticRAG.py                    # Improved implementation
├── onlysearchAuthenticRAG.py          # NEW: Search-only mode
├── test_advanced_questions.py         # NEW: Test suite
├── demo_check_system.py               # NEW: System verification
└── corpus_input/                      # Organized document storage
```

#### Key Improvements

1. **Better Organization**
   - Separated concerns (indexing vs searching)
   - Dedicated test suite
   - Helper scripts for setup and verification

2. **Enhanced Features**
   - Contextual Retrieval implementation
   - Hybrid Search (BM25 + Vector + RRF)
   - Better Thai language support
   - Comprehensive testing framework

3. **Developer Experience**
   - `setup.sh` for easy installation
   - `demo_check_system.py` for verification
   - `QUICKSTART.md` for quick onboarding
   - Detailed documentation

#### Migration Steps

**Step 1: Backup Old Data**
```bash
# Old files already moved to archive/
# Check archive/README.md for details
```

**Step 2: Setup New Environment**
```bash
cd AuthenticRAG-Qwen2.5API
./setup.sh
python demo_check_system.py
```

**Step 3: Verify Existing Index**
```bash
# Check if your 53 documents are still indexed
curl -X GET "localhost:9200/contextual_chunks/_count?pretty"
```

**Step 4: Use New Scripts**
```bash
# For search only (recommended)
python onlysearchAuthenticRAG.py

# For full re-indexing (if needed)
python authenticRAG.py
```

#### Breaking Changes

⚠️ **API Changes:**
- Old: Single monolithic script
- New: Separated indexing and search scripts

⚠️ **Configuration:**
- API key now required in script (not environment variable)
- OpenSearch index name: `contextual_chunks` (unchanged)

⚠️ **Dependencies:**
- Added: `sentence-transformers`, `llama-index`, `langchain`
- Updated: `opensearch-py` to 2.7.1

#### Backward Compatibility

✅ **Compatible:**
- OpenSearch index structure (no migration needed)
- Document format (Markdown)
- Embedding model (BAAI/bge-m3)

❌ **Not Compatible:**
- Old script command-line arguments
- Environment variable configuration

---

## 🗺️ Development Roadmap

### Current Status (v1.0.0 - March 2026)

✅ **Completed Features:**
- Contextual Retrieval implementation
- Hybrid Search (BM25 + Vector + RRF)
- Thai language support
- Test suite with 15 advanced questions
- Comprehensive documentation
- System verification tools

📊 **Current Metrics:**
- 53 documents indexed
- 2-3 seconds query time
- 1024-dimensional embeddings
- Support for 4 medical topics

---

### Phase 1: Performance Optimization (Q2 2026)

**Goals:**
- Reduce query time to <1 second
- Improve search relevance by 10%
- Optimize memory usage

**Tasks:**
- [ ] Implement query caching
- [ ] Optimize embedding batch processing
- [ ] Add connection pooling for OpenSearch
- [ ] Profile and optimize bottlenecks

**Code Changes:**
```python
# Add caching layer
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str) -> List[Dict]:
    # Cache frequent queries
    pass
```

---

### Phase 2: Enhanced Features (Q3 2026)

**Goals:**
- Support more document formats
- Add real-time indexing
- Implement feedback loop

**Tasks:**
- [ ] PDF document support
- [ ] DOCX document support
- [ ] Real-time document monitoring
- [ ] User feedback collection
- [ ] Answer quality scoring

**New Components:**
```python
# Document processors
class PDFProcessor:
    def extract_text(self, pdf_path: str) -> str:
        pass

class DOCXProcessor:
    def extract_text(self, docx_path: str) -> str:
        pass

# Feedback system
class FeedbackCollector:
    def record_feedback(self, query: str, answer: str, rating: int):
        pass
```

---

### Phase 3: API & Integration (Q4 2026)

**Goals:**
- RESTful API endpoint ✅ COMPLETED
- Web interface ✅ COMPLETED
- Docker deployment

**Tasks:**
- [x] FastAPI implementation
- [x] Swagger documentation
- [x] Streamlit frontend
- [ ] Docker containerization
- [ ] CI/CD pipeline

**Completed Components:**
```python
# FastAPI Backend (api_server.py)
- POST /search - Hybrid search endpoint
- POST /answer - Question answering endpoint
- GET /health - Health check
- GET /stats - System statistics
- Swagger UI at /docs

# Streamlit Frontend (streamlit_app.py)
- Answer mode with AI-generated responses
- Search mode with adjustable weights
- Real-time system monitoring
- Search history tracking
- Responsive UI design
```

**Next Steps:**
```dockerfile
# Docker deployment
FROM python:3.10-slim
WORKDIR /app
COPY requirements-ui.txt .
RUN pip install -r requirements-ui.txt
COPY . .
CMD ["./start_ui.sh"]
```

---

### Phase 4: Advanced AI Features (2027)

**Goals:**
- Multi-modal support (images, tables)
- Fine-tuned domain model
- Advanced reasoning

**Tasks:**
- [ ] Image understanding (OCR + Vision models)
- [ ] Table extraction and understanding
- [ ] Fine-tune embedding model on medical corpus
- [ ] Implement chain-of-thought reasoning
- [ ] Multi-hop question answering

**Research Areas:**
- Vision-Language models for medical images
- Graph-based reasoning for complex queries
- Active learning for continuous improvement

---

### Phase 5: Enterprise Features (2027+)

**Goals:**
- Multi-tenancy support
- Advanced security
- Scalability

**Tasks:**
- [ ] User authentication & authorization
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Horizontal scaling
- [ ] Load balancing
- [ ] Data encryption

---

## 🎯 Development Priorities

### High Priority (Next 3 Months)
1. **Performance Optimization**
   - Query caching
   - Batch processing
   - Connection pooling

2. **Testing & Quality**
   - Increase test coverage to 80%
   - Add integration tests
   - Performance benchmarks

3. **Documentation**
   - API documentation
   - Architecture diagrams
   - Video tutorials

### Medium Priority (3-6 Months)
1. **Feature Enhancement**
   - PDF/DOCX support
   - Real-time indexing
   - Feedback system

2. **Developer Tools**
   - CLI tool for management
   - Monitoring dashboard
   - Debug utilities

### Low Priority (6-12 Months)
1. **Advanced Features**
   - Multi-modal support
   - Fine-tuned models
   - Advanced reasoning

2. **Enterprise Features**
   - Multi-tenancy
   - Advanced security
   - Scalability

---

## 🔧 Technical Debt & Known Issues

### Current Technical Debt

1. **Code Organization**
   - [ ] Refactor monolithic scripts into modules
   - [ ] Separate configuration from code
   - [ ] Implement proper logging

2. **Testing**
   - [ ] Add unit tests for core functions
   - [ ] Add integration tests
   - [ ] Add performance tests

3. **Error Handling**
   - [ ] Improve error messages
   - [ ] Add retry logic for API calls
   - [ ] Better exception handling

### Known Issues

1. **Performance**
   - Query time varies with document count
   - Memory usage increases with large documents
   - No query timeout mechanism

2. **Functionality**
   - Limited to Markdown documents
   - No support for images/tables
   - Single-language answer generation

3. **Deployment**
   - Manual setup required
   - No containerization
   - No automated deployment

---

## 📊 Metrics & Monitoring

### Current Metrics to Track

```python
# Add to your code
import time
import logging

class MetricsCollector:
    def __init__(self):
        self.query_times = []
        self.search_scores = []
        
    def record_query(self, query_time: float, score: float):
        self.query_times.append(query_time)
        self.search_scores.append(score)
        
    def get_stats(self):
        return {
            "avg_query_time": sum(self.query_times) / len(self.query_times),
            "avg_score": sum(self.search_scores) / len(self.search_scores),
            "total_queries": len(self.query_times)
        }
```

### Recommended Monitoring

1. **Performance Metrics**
   - Query latency (p50, p95, p99)
   - Indexing throughput
   - Memory usage
   - CPU usage

2. **Quality Metrics**
   - Search relevance scores
   - Answer accuracy (from feedback)
   - Document coverage

3. **System Metrics**
   - OpenSearch cluster health
   - API availability
   - Error rates

---

## 🚀 Getting Started with Development

### For New Developers

1. **Read Documentation**
   - This README-DEV.md
   - CHANGELOG.md for recent changes
   - README-USER.md for user perspective

2. **Setup Environment**
   ```bash
   cd AuthenticRAG-Qwen2.5API
   ./setup.sh
   python demo_check_system.py
   ```

3. **Run Tests**
   ```bash
   python test_advanced_questions.py
   ```

4. **Make Changes**
   - Create feature branch
   - Write tests first (TDD)
   - Implement feature
   - Update documentation

5. **Submit PR**
   - Ensure tests pass
   - Update CHANGELOG.md
   - Request review

### Development Workflow

```bash
# 1. Create branch
git checkout -b feature/your-feature

# 2. Make changes
# ... edit code ...

# 3. Test
python test_advanced_questions.py

# 4. Commit
git add .
git commit -m "feat: add your feature"

# 5. Push
git push origin feature/your-feature

# 6. Create PR
```

---

## 📚 References

- [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [BGE-M3 Model](https://huggingface.co/BAAI/bge-m3)
- [Qwen API](https://aiforthai.in.th/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'feat: Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Commit Message Convention

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
refactor: Refactor code
perf: Performance improvement
chore: Maintenance tasks
```

## 📄 License

[Specify your license here]

## 👥 Authors & Maintainers

- **Development Team**: Initial implementation
- **Maintainer**: [Your Name]
- **Contact**: [your-email@example.com]

## 🙏 Acknowledgments

- Anthropic for Contextual Retrieval technique
- BAAI for BGE-M3 embedding model
- OpenSearch community
- AI For Thai for Qwen API access
- All contributors and testers

---

**Version**: 1.0.0  
**Last Updated**: March 7, 2026  
**Status**: ✅ Production Ready

---

*For user documentation, see [README-USER.md](README-USER.md)*  
*For change history, see [CHANGELOG.md](CHANGELOG.md)*
