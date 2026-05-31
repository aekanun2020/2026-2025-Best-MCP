#!/bin/bash

# Test script for add_context tool
echo "Testing add_context tool..."

# Test 1: Basic context addition
echo "Test 1: Adding basic context..."
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add_context",
      "arguments": {
        "content": "ผู้ใช้ถามเกี่ยวกับขั้นตอนการสมัครงาน และได้รับคำตอบว่าต้องส่งเอกสาร 3 ชิ้น คือ ใบสมัคร, ประวัติ, และใบรับรอง การสมัครต้องทำผ่านระบบออนไลน์ และมีกำหนดเวลา 30 วัน",
        "title": "Q&A: ขั้นตอนการสมัครงาน",
        "source": "chat_conversation"
      }
    }
  }'

echo -e "\n\n"

# Test 2: Context with metadata
echo "Test 2: Adding context with metadata..."
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "add_context",
      "arguments": {
        "content": "Agent ได้ช่วยผู้ใช้แก้ปัญหาการเชื่อมต่อฐานข้อมูล โดยแนะนำให้ตรวจสอบ connection string และ firewall settings ผลลัพธ์คือสามารถเชื่อมต่อได้สำเร็จ",
        "title": "Troubleshooting: Database Connection",
        "source": "technical_support",
        "metadata": {
          "conversation_id": "conv_456",
          "user_id": "user_789",
          "issue_type": "database",
          "resolution_status": "resolved"
        }
      }
    }
  }'

echo -e "\n\n"

# Test 3: Search for added context
echo "Test 3: Searching for added context..."
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "การสมัครงาน",
        "limit": 3,
        "search_mode": "hybrid"
      }
    }
  }'

echo -e "\n\n"

# Test 4: Search for technical context
echo "Test 4: Searching for technical context..."
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "database connection",
        "limit": 3,
        "search_mode": "semantic"
      }
    }
  }'

echo -e "\n\nTest completed!"