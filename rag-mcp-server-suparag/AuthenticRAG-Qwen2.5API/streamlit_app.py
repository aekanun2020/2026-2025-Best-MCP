#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit UI for AuthenticRAG
Web interface for search, question answering, and document management
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8001"
CORPUS_DIR = "/app/corpus_input"  # Inside container

# Page config
st.set_page_config(
    page_title="AuthenticRAG - ระบบค้นหาและจัดการเอกสาร",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .source-card {
        background-color: #e8eaf6;
        padding: 0.8rem;
        border-radius: 0.3rem;
        margin-top: 0.5rem;
        border-left: 3px solid #1f77b4;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .doc-item {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    .doc-item:hover {
        border-color: #1f77b4;
        box-shadow: 0 2px 4px rgba(31,119,180,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = "search"

def check_api_health():
    """ตรวจสอบสถานะ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except:
        return False, None

def search_documents(query, top_k=10, final_top_k=5, sparse_weight=0.5, dense_weight=0.5):
    """ค้นหาเอกสาร"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/search",
            json={
                "query": query,
                "top_k": top_k,
                "final_top_k": final_top_k,
                "sparse_weight": sparse_weight,
                "dense_weight": dense_weight
            },
            timeout=30
        )
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

def get_answer(query, top_k=10, final_top_k=5):
    """รับคำตอบจากระบบ"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/answer",
            json={
                "query": query,
                "top_k": top_k,
                "final_top_k": final_top_k
            },
            timeout=60
        )
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

def get_stats():
    """ดึงสถิติระบบ"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except:
        return False, None

# Document Management Functions
def list_documents():
    """แสดงรายการเอกสารทั้งหมด"""
    try:
        if not os.path.exists(CORPUS_DIR):
            os.makedirs(CORPUS_DIR, exist_ok=True)
        
        files = []
        for file in Path(CORPUS_DIR).glob("*.md"):
            stat = file.stat()
            files.append({
                'name': file.name,
                'path': str(file),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)
    except Exception as e:
        st.error(f"Error listing documents: {e}")
        return []

def save_document(filename, content):
    """บันทึกเอกสาร"""
    try:
        if not os.path.exists(CORPUS_DIR):
            os.makedirs(CORPUS_DIR, exist_ok=True)
        
        filepath = os.path.join(CORPUS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, "บันทึกเอกสารสำเร็จ"
    except Exception as e:
        return False, f"Error saving document: {e}"

def read_document(filename):
    """อ่านเอกสาร"""
    try:
        filepath = os.path.join(CORPUS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return True, f.read()
    except Exception as e:
        return False, f"Error reading document: {e}"

def delete_document(filename):
    """ลบเอกสาร"""
    try:
        filepath = os.path.join(CORPUS_DIR, filename)
        os.remove(filepath)
        return True, "ลบเอกสารสำเร็จ"
    except Exception as e:
        return False, f"Error deleting document: {e}"

def format_file_size(size_bytes):
    """แปลงขนาดไฟล์เป็นรูปแบบที่อ่านง่าย"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

# Sidebar
with st.sidebar:
    st.markdown("### 📑 เมนู")
    
    # Page Navigation
    page = st.radio(
        "เลือกหน้า",
        ["🔍 ค้นหา", "📁 จัดการเอกสาร"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # API Health Check
    st.markdown("#### 🏥 สถานะระบบ")
    health_ok, health_data = check_api_health()
    
    if health_ok:
        st.success("✅ ระบบพร้อมใช้งาน")
        if health_data:
            st.metric("เอกสารในระบบ", health_data.get('documents_indexed', 0))
    else:
        st.error("❌ ไม่สามารถเชื่อมต่อ API")
        st.info("กรุณาเริ่ม API Server")
    
    st.markdown("---")
    
    if page == "🔍 ค้นหา":
        # Search Settings
        st.markdown("#### 🔍 การตั้งค่าการค้นหา")
        
        mode = st.radio(
            "โหมดการทำงาน",
            ["ตอบคำถาม", "ค้นหาเอกสาร"],
            help="เลือกโหมดการทำงาน"
        )
        
        top_k = st.slider(
            "จำนวนเอกสารที่ค้นหา",
            min_value=5,
            max_value=50,
            value=10,
            step=5,
            help="จำนวนเอกสารที่จะค้นหาจาก OpenSearch"
        )
        
        final_top_k = st.slider(
            "จำนวนเอกสารสุดท้าย",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="จำนวนเอกสารที่จะใช้สร้างคำตอบ"
        )
        
        if mode == "ค้นหาเอกสาร":
            st.markdown("#### ⚖️ น้ำหนักการค้นหา")
            
            sparse_weight = st.slider(
                "BM25 Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="น้ำหนักสำหรับการค้นหาแบบ keyword"
            )
            
            dense_weight = st.slider(
                "Vector Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="น้ำหนักสำหรับการค้นหาแบบ semantic"
            )
    
    st.markdown("---")
    
    # Statistics
    st.markdown("#### 📊 สถิติ")
    docs = list_documents()
    st.metric("ไฟล์ในโฟลเดอร์", len(docs))
    
    total_size = sum(doc['size'] for doc in docs)
    st.metric("ขนาดรวม", format_file_size(total_size))
    
    st.markdown("---")
    
    # Clear History
    if page == "🔍 ค้นหา":
        if st.button("🗑️ ล้างประวัติ", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# Main Content
st.markdown('<div class="main-header">🔍 AuthenticRAG</div>', unsafe_allow_html=True)

if page == "🔍 ค้นหา":
    st.markdown('<p style="text-align: center; color: #666;">ระบบค้นหาและตอบคำถามด้วย Contextual RAG</p>', unsafe_allow_html=True)
    
    # Input Section
    st.markdown("### 💬 ถามคำถามหรือค้นหาเอกสาร")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "คำถามหรือคำค้นหา",
            placeholder="พิมพ์คำถามหรือคำค้นหาที่นี่...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 ค้นหา", use_container_width=True, type="primary")
    
    # Example Questions
    with st.expander("💡 ตัวอย่างคำถาม"):
        example_questions = [
            "โรคหัดเยอรมันคืออะไร?",
            "อาการของโรคต้อกระจกมีอะไรบ้าง?",
            "วิธีป้องกันโรคกรดไหลย้อน",
            "อหิวาตกโรคเกิดจากอะไร?",
            "โรคหัดเยอรมันกับหญิงตั้งครรภ์"
        ]
        
        cols = st.columns(len(example_questions))
        for i, (col, q) in enumerate(zip(cols, example_questions)):
            if col.button(q, key=f"example_{i}", use_container_width=True):
                query = q
                search_button = True
    
    # Process Query
    if search_button and query:
        with st.spinner("🔄 กำลังประมวลผล..."):
            start_time = time.time()
            
            if mode == "ตอบคำถาม":
                # Get Answer
                success, result = get_answer(query, top_k, final_top_k)
                
                if success:
                    elapsed_time = time.time() - start_time
                    
                    # Add to history
                    st.session_state.history.insert(0, {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'query': query,
                        'mode': mode,
                        'result': result
                    })
                    
                    # Display Answer
                    st.markdown("### 💡 คำตอบ")
                    st.markdown(f'<div class="result-card">{result["answer"]}</div>', unsafe_allow_html=True)
                    
                    # Display Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("เวลาที่ใช้", f"{elapsed_time:.2f} วินาที")
                    with col2:
                        st.metric("เอกสารที่ใช้", len(result.get('sources', [])))
                    with col3:
                        st.metric("โหมด", "ตอบคำถาม")
                    
                    # Display Sources
                    st.markdown("### 📚 แหล่งอ้างอิง")
                    for i, source in enumerate(result.get('sources', []), 1):
                        with st.expander(f"เอกสารที่ {i} (Score: {source['score']:.4f})"):
                            st.markdown(f"**Doc ID:** `{source['doc_id']}`")
                            st.markdown("**เนื้อหา:**")
                            st.text_area(
                                "content",
                                source['content'],
                                height=150,
                                key=f"source_{i}",
                                label_visibility="collapsed"
                            )
                            if source.get('context'):
                                st.markdown("**บริบท:**")
                                st.info(source['context'])
                else:
                    st.error(f"❌ เกิดข้อผิดพลาด: {result.get('error', 'Unknown error')}")
            
            else:
                # Search Documents
                success, result = search_documents(query, top_k, final_top_k, sparse_weight, dense_weight)
                
                if success:
                    elapsed_time = time.time() - start_time
                    
                    # Add to history
                    st.session_state.history.insert(0, {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'query': query,
                        'mode': mode,
                        'result': result
                    })
                    
                    # Display Results
                    st.markdown("### 🔍 ผลการค้นหา")
                    
                    # Display Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("เวลาที่ใช้", f"{result['search_time']:.2f} วินาที")
                    with col2:
                        st.metric("เอกสารที่พบ", result['total_results'])
                    with col3:
                        st.metric("โหมด", "ค้นหาเอกสาร")
                    
                    # Display Documents
                    for i, doc in enumerate(result.get('results', []), 1):
                        with st.expander(f"📄 เอกสารที่ {i} (Score: {doc['score']:.4f})", expanded=(i==1)):
                            st.markdown(f"**Doc ID:** `{doc['doc_id']}`")
                            st.markdown("**เนื้อหา:**")
                            st.text_area(
                                "content",
                                doc['content'],
                                height=150,
                                key=f"doc_{i}",
                                label_visibility="collapsed"
                            )
                            if doc.get('context'):
                                st.markdown("**บริบท:**")
                                st.info(doc['context'])
                else:
                    st.error(f"❌ เกิดข้อผิดพลาด: {result.get('error', 'Unknown error')}")
    
    # History Section
    if st.session_state.history:
        st.markdown("---")
        st.markdown("### 📜 ประวัติการค้นหา")
        
        for i, item in enumerate(st.session_state.history[:5]):  # Show last 5
            with st.expander(f"🕐 {item['timestamp']} - {item['query'][:50]}..."):
                st.markdown(f"**คำค้นหา:** {item['query']}")
                st.markdown(f"**โหมด:** {item['mode']}")
                
                if item['mode'] == "ตอบคำถาม":
                    st.markdown("**คำตอบ:**")
                    st.info(item['result']['answer'])
                else:
                    st.markdown(f"**ผลลัพธ์:** {item['result']['total_results']} เอกสาร")

else:  # Document Management Page
    st.markdown('<p style="text-align: center; color: #666;">จัดการเอกสารในระบบ</p>', unsafe_allow_html=True)
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 รายการเอกสาร", "➕ เพิ่มเอกสาร", "✏️ แก้ไขเอกสาร"])
    
    with tab1:
        st.markdown("### 📋 รายการเอกสารทั้งหมด")
        
        docs = list_documents()
        
        if not docs:
            st.info("ยังไม่มีเอกสารในระบบ กรุณาเพิ่มเอกสารใหม่")
        else:
            st.markdown(f"**จำนวนเอกสาร:** {len(docs)} ไฟล์")
            
            # Display documents
            for doc in docs:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**📄 {doc['name']}**")
                
                with col2:
                    st.text(format_file_size(doc['size']))
                
                with col3:
                    st.text(doc['modified'])
                
                with col4:
                    if st.button("🗑️", key=f"delete_{doc['name']}", help="ลบเอกสาร"):
                        success, message = delete_document(doc['name'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                st.markdown("---")
    
    with tab2:
        st.markdown("### ➕ เพิ่มเอกสารใหม่")
        
        # Method selection
        upload_method = st.radio(
            "เลือกวิธีการเพิ่มเอกสาร",
            ["📤 อัปโหลดไฟล์", "✍️ เขียนเอง"],
            horizontal=True
        )
        
        if upload_method == "📤 อัปโหลดไฟล์":
            uploaded_file = st.file_uploader(
                "เลือกไฟล์ Markdown (.md)",
                type=['md'],
                help="อัปโหลดไฟล์ .md เท่านั้น"
            )
            
            if uploaded_file is not None:
                # Show preview
                content = uploaded_file.read().decode('utf-8')
                
                st.markdown("#### 👀 ตัวอย่างเนื้อหา")
                st.text_area(
                    "preview",
                    content,
                    height=300,
                    label_visibility="collapsed",
                    disabled=True
                )
                
                # Save button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 บันทึก", type="primary", use_container_width=True, key="save_upload"):
                        success, message = save_document(uploaded_file.name, content)
                        if success:
                            st.success(f"✅ {message}: {uploaded_file.name}")
                            st.balloons()
                        else:
                            st.error(message)
        
        else:  # Write manually
            filename = st.text_input(
                "ชื่อไฟล์",
                placeholder="example.md",
                help="ต้องลงท้ายด้วย .md"
            )
            
            content = st.text_area(
                "เนื้อหาเอกสาร (Markdown)",
                height=400,
                placeholder="# หัวข้อ\n\nเนื้อหา...",
                help="เขียนเนื้อหาในรูปแบบ Markdown"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 บันทึก", type="primary", use_container_width=True, key="save_manual"):
                    if not filename:
                        st.error("กรุณาระบุชื่อไฟล์")
                    elif not filename.endswith('.md'):
                        st.error("ชื่อไฟล์ต้องลงท้ายด้วย .md")
                    elif not content:
                        st.error("กรุณาใส่เนื้อหา")
                    else:
                        success, message = save_document(filename, content)
                        if success:
                            st.success(f"✅ {message}: {filename}")
                            st.balloons()
                        else:
                            st.error(message)
    
    with tab3:
        st.markdown("### ✏️ แก้ไขเอกสาร")
        
        docs = list_documents()
        
        if not docs:
            st.info("ยังไม่มีเอกสารในระบบ")
        else:
            # Select document to edit
            doc_names = [doc['name'] for doc in docs]
            selected_doc = st.selectbox(
                "เลือกเอกสารที่ต้องการแก้ไข",
                doc_names
            )
            
            if selected_doc:
                # Read document
                success, content = read_document(selected_doc)
                
                if success:
                    # Show file info
                    doc_info = next(d for d in docs if d['name'] == selected_doc)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("ขนาดไฟล์", format_file_size(doc_info['size']))
                    with col2:
                        st.metric("แก้ไขล่าสุด", doc_info['modified'])
                    
                    st.markdown("---")
                    
                    # Edit content
                    new_content = st.text_area(
                        "เนื้อหาเอกสาร",
                        value=content,
                        height=400,
                        help="แก้ไขเนื้อหาได้เลย"
                    )
                    
                    # Save button
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        if st.button("💾 บันทึก", type="primary", use_container_width=True, key="save_edit"):
                            success, message = save_document(selected_doc, new_content)
                            if success:
                                st.success(f"✅ {message}: {selected_doc}")
                            else:
                                st.error(message)
                    
                    with col2:
                        if st.button("🔄 รีเซ็ต", use_container_width=True):
                            st.rerun()
                else:
                    st.error(content)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>AuthenticRAG v2.0.0 | Powered by Qwen API + OpenSearch + BGE-M3</p>
    <p>📚 <a href="https://github.com/aekanun2020/2026-ContextualRAG" target="_blank">GitHub</a> | 
    📖 <a href="http://localhost:9001/health" target="_blank">API Health</a></p>
</div>
""", unsafe_allow_html=True)
