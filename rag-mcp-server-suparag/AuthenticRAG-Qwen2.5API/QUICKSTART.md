# 🚀 Quick Start Guide

## Prerequisites

1. **Python 3.8+** installed
2. **Docker Desktop** running
3. **DashScope API Key** from Alibaba Cloud

## Step 1: Start OpenSearch

```bash
# Create Docker network
docker network create opensearch-net

# Start OpenSearch (macOS/Linux)
docker run -e OPENSEARCH_JAVA_OPTS="-Xms512m -Xmx512m" \
  -e discovery.type="single-node" \
  -e DISABLE_SECURITY_PLUGIN="true" \
  -e bootstrap.memory_lock="true" \
  -e cluster.name="opensearch-cluster" \
  -e node.name="os01" \
  -e plugins.neural_search.hybrid_search_disabled="true" \
  -e DISABLE_INSTALL_DEMO_CONFIG="true" \
  --ulimit nofile="65536:65536" \
  --ulimit memlock="-1:-1" \
  --net opensearch-net \
  --restart=no \
  -v opensearch-data:/usr/share/opensearch/data \
  -p 9200:9200 \
  --name=opensearch-single-node \
  opensearchproject/opensearch:latest
```

Wait for OpenSearch to start (check with `curl http://localhost:9200`)

## Step 2: Set API Key

```bash
export DASHSCOPE_API_KEY='your_api_key_here'
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the setup script:

```bash
./setup.sh
```

## Step 4: Run the System

### Option A: Full System (Index + Search)

```bash
python authenticRAG.py
```

This will:
1. Load documents from `corpus_input/`
2. Generate contextual embeddings using Qwen API
3. Index documents into OpenSearch
4. Run sample queries

### Option B: Search Only (if index already exists)

```bash
python onlysearchAuthenticRAG.py
```

This will search the existing index with predefined questions.

## Expected Output

You should see:
- ✅ Document loading progress
- ✅ Context generation for each chunk
- ✅ Indexing progress
- ✅ Search results with scores
- ✅ AI-generated answers

## Troubleshooting

### OpenSearch not running
```bash
docker ps | grep opensearch
```

### API Key not set
```bash
echo $DASHSCOPE_API_KEY
```

### Dependencies missing
```bash
pip install -r requirements.txt
```

## Next Steps

- Modify questions in the Python files
- Add your own documents to `corpus_input/`
- Adjust chunk size in `MarkdownNodeParser(chunk_size=256)`
- Change the number of results with `k=5` parameter

Enjoy! 🎉
