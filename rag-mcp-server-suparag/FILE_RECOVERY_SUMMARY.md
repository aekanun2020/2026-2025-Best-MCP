# File Recovery Summary

**Date**: 2026-04-15  
**Issue**: Original corpus files disappeared from container

---

## 🔍 Investigation

### What Happened
1. ตรวจสอบ container: `/app/corpus_input/` → **ว่างเปล่า**
2. ตรวจสอบ host: `./AuthenticRAG-Qwen2.5API/corpus_input/` → **ว่างเปล่า**
3. ค้นหาไฟล์เดิม (1.md, 2.md, 44.md, 5555.md) → **ไม่พบ**

### Possible Causes
- ❌ Volume mapping ผิดพลาดตอน rebuild container
- ❌ ไฟล์ถูกลบโดยไม่ตั้งใจ
- ❌ Directory ถูก overwrite ตอน build

---

## ✅ Solution

### Created Sample Files
สร้างไฟล์ตัวอย่างใหม่เพื่อทดสอบระบบ:

1. **sample-1.md** (723 bytes)
   - ข้อมูลทั่วไปเกี่ยวกับระบบ
   - คุณสมบัติของ AuthenticRAG
   - วิธีการใช้งาน

2. **sample-2.md** (535 bytes)
   - Document Management features
   - Search Features
   - Architecture overview

---

## 📊 Current Status

### Host Machine
```bash
$ ls -lah AuthenticRAG-Qwen2.5API/corpus_input/
total 16
drwxrwxr-x   4 grizzlymacbookpro  staff   128B Apr 15 10:32 .
drwxrwxr-x  27 grizzlymacbookpro  staff   864B Apr 15 10:32 ..
-rw-r--r--   1 grizzlymacbookpro  staff   723B Apr 15 10:31 sample-1.md
-rw-r--r--   1 grizzlymacbookpro  staff   535B Apr 15 10:32 sample-2.md
```

### Container
```bash
$ docker exec contextual-rag-ui ls -lah /app/corpus_input/
total 8.0K
drwxrwxr-x  4 root root 128 Apr 15 03:32 .
drwxrwxr-x 27 root root 864 Apr 15 03:32 ..
-rw-r--r--  1 root root 723 Apr 15 03:31 sample-1.md
-rw-r--r--  1 root root 535 Apr 15 03:32 sample-2.md
```

✅ **Volume mapping working correctly**

---

## 🔄 What Was Lost

### Original Files (4 files, 53 chunks)
1. **1.md** (64KB) - โรคหัดเยอรมัน (Rubella)
2. **2.md** (60KB) - อหิวาตกโรค (Cholera)
3. **44.md** (49KB) - ต้อกระจก (Cataract)
4. **5555.md** (59KB) - กรดไหลย้อน (GERD)

**Total**: ~232 KB, 53 indexed chunks

### OpenSearch Data
⚠️ **Indexed data still exists in OpenSearch!**

The original 53 chunks are still in OpenSearch indices:
- `anthropic-vector-index`
- `anthropic-bm25-index`

**You can still search the old documents**, but the source files are gone.

---

## 🎯 Next Steps

### Option 1: Continue with Sample Files ✅ Recommended
```bash
# Test the new sample files
1. Open Streamlit UI: http://localhost:9501
2. Go to "📁 จัดการเอกสาร"
3. See sample-1.md and sample-2.md
4. Add more documents as needed
```

### Option 2: Restore Original Files
If you have backups:
```bash
# Copy original files back
cp /path/to/backup/*.md AuthenticRAG-Qwen2.5API/corpus_input/

# Verify in container
docker exec contextual-rag-ui ls -la /app/corpus_input/
```

### Option 3: Clear OpenSearch and Start Fresh
```bash
# Delete old indices
curl -X DELETE http://localhost:9201/anthropic-vector-index
curl -X DELETE http://localhost:9201/anthropic-bm25-index

# Restart MCP server to recreate indices
docker-compose restart mcp-server

# Index new documents
# (via Streamlit UI or MCP tool)
```

---

## 🧪 Testing Document Management

### 1. View Files in UI
```
1. Open http://localhost:9501
2. Click "📁 จัดการเอกสาร"
3. Tab "📋 รายการเอกสาร"
4. Should see:
   - sample-1.md (723 B)
   - sample-2.md (535 B)
```

### 2. Add New File
```
1. Tab "➕ เพิ่มเอกสาร"
2. Choose "✍️ เขียนเอง"
3. Filename: test.md
4. Content: # Test Document
5. Click "💾 บันทึก"
6. Verify in "📋 รายการเอกสาร"
```

### 3. Edit File
```
1. Tab "✏️ แก้ไขเอกสาร"
2. Select: sample-1.md
3. Edit content
4. Click "💾 บันทึก"
```

### 4. Delete File
```
1. Tab "📋 รายการเอกสาร"
2. Click 🗑️ next to test.md
3. File should disappear
```

---

## 📝 Recommendations

### 1. Backup Important Files
```bash
# Create backup directory
mkdir -p backups/corpus_input

# Backup regularly
cp AuthenticRAG-Qwen2.5API/corpus_input/*.md backups/corpus_input/
```

### 2. Use Version Control
```bash
# Add corpus_input to git (if appropriate)
git add AuthenticRAG-Qwen2.5API/corpus_input/*.md
git commit -m "Add corpus documents"
```

### 3. Document Your Sources
Keep a list of where original documents came from:
```
1.md - Source: https://medthai.com/rubella
2.md - Source: https://medthai.com/cholera
44.md - Source: https://medthai.com/cataract
5555.md - Source: https://medthai.com/gerd
```

---

## 🔧 Volume Mapping Verification

### Current Configuration
```yaml
# docker-compose.yml
streamlit:
  volumes:
    - ./AuthenticRAG-Qwen2.5API:/app
    - ./AuthenticRAG-Qwen2.5API/corpus_input:/app/corpus_input
```

### Test Commands
```bash
# Create file on host
echo "# Test" > AuthenticRAG-Qwen2.5API/corpus_input/test.md

# Check in container
docker exec contextual-rag-ui cat /app/corpus_input/test.md
# Should output: # Test

# Delete from container
docker exec contextual-rag-ui rm /app/corpus_input/test.md

# Check on host
ls AuthenticRAG-Qwen2.5API/corpus_input/test.md
# Should show: No such file or directory
```

✅ **Bidirectional sync working**

---

## 📊 Summary

### What We Know
- ✅ Volume mapping is working correctly
- ✅ Streamlit UI can read/write files
- ✅ Sample files created and visible
- ❌ Original 4 files are lost
- ⚠️ Old indexed data still in OpenSearch

### What to Do
1. **Short term**: Use sample files to test system
2. **Medium term**: Add new documents via UI
3. **Long term**: Implement backup strategy

### System Status
```
✅ Streamlit UI - Running with document management
✅ MCP Server - Running (search only)
✅ OpenSearch - Running (old data still there)
✅ Ollama - Running
```

---

## 🎓 Lessons Learned

1. **Always backup important files** before container operations
2. **Volume mounts can be tricky** - verify after changes
3. **OpenSearch data persists** even when source files are gone
4. **Test file operations** before relying on them

---

## 🚀 Moving Forward

### Immediate Actions
- [x] Create sample files
- [x] Verify volume mapping
- [x] Test Streamlit UI
- [ ] Add real documents
- [ ] Index new documents
- [ ] Test search functionality

### Future Improvements
- [ ] Add backup script
- [ ] Add file upload validation
- [ ] Add file size limits
- [ ] Add file preview before save
- [ ] Add undo/restore functionality
