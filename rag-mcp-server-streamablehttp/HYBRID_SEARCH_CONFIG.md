# Hybrid Search Configuration Guide

## Performance Tuning for Large Document Collections

### Current Implementation (Default)
- **Build Time:** On server startup
- **Strategy:** Load all documents at once
- **Best for:** < 50K documents

### For Large Collections (> 50K documents)

#### Option 1: Increase Batch Size
```python
# In main.py - build_bm25_index()
batch_size = 5000  # Default: 1000
```

#### Option 2: Lazy Loading (Future Enhancement)
Build BM25 index in background after server starts:
```python
# Start server immediately
# Build BM25 index asynchronously
# Use semantic-only until BM25 ready
```

#### Option 3: Persistent BM25 Index (Future Enhancement)
Save BM25 index to disk:
```python
# Save: pickle.dump(bm25_index, file)
# Load: pickle.load(file)
# Faster startup, but needs disk space
```

## Memory Estimates

| Documents | Memory Usage | Build Time |
|-----------|--------------|------------|
| 1K        | ~1-5 MB      | ~0.1s      |
| 10K       | ~10-50 MB    | ~1s        |
| 50K       | ~50-250 MB   | ~5s        |
| 100K      | ~100-500 MB  | ~10s       |
| 500K      | ~500MB-2.5GB | ~50s       |
| 1M        | ~1-5 GB      | ~100s      |

## Monitoring

Check BM25 index status:
```bash
# View startup logs
docker-compose logs pyragdoc | grep "BM25"

# Expected output:
# Building BM25 index from existing documents...
# Loaded 1000 documents from Qdrant...
# Loaded 2000 documents from Qdrant...
# Building BM25 index for 7 documents...
# ✅ BM25 index built successfully with 7 documents
```

## Troubleshooting

### Startup Too Slow
- Reduce batch_size
- Consider lazy loading
- Use persistent index

### Out of Memory
- Reduce document count
- Use pagination
- Increase container memory limit

### BM25 Index Failed
- Server continues with semantic-only search
- Check logs for errors
- Hybrid search falls back to semantic mode
