# Add Context Tool Guide

## Overview

Tool `add_context` ช่วยให้ agent สามารถเก็บ context ที่ได้รับจากการสนทนาหรือการทำงานลงใน vector database ได้โดยตรง ทำให้ข้อมูลเหล่านี้สามารถค้นหาและใช้งานได้ในอนาคต

## Use Cases

### 1. เก็บ Q&A จากการสนทนา
เมื่อ agent ตอบคำถามผู้ใช้ สามารถเก็บคำถาม-คำตอบไว้เป็น knowledge base

### 2. บันทึกการแก้ปัญหา
เก็บขั้นตอนการแก้ปัญหาที่ agent ได้ช่วยผู้ใช้แก้ไข

### 3. สร้าง Knowledge Base แบบ Dynamic
เก็บข้อมูลที่ได้จากการทำงานจริงเพื่อปรับปรุง knowledge base

### 4. เก็บ Context จาก External Sources
เมื่อ agent ได้ข้อมูลจาก API หรือแหล่งข้อมูลภายนอก

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content` | string | ✅ | - | เนื้อหาที่ต้องการเก็บ |
| `title` | string | ❌ | auto-generated | หัวข้อของเนื้อหา |
| `source` | string | ❌ | "agent_context" | แหล่งที่มาของข้อมูล |
| `metadata` | object | ❌ | {} | ข้อมูลเพิ่มเติม |

## Examples

### Basic Usage
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "add_context",
    "arguments": {
      "content": "ผู้ใช้ถามเกี่ยวกับการติดตั้ง Docker และได้รับคำแนะนำให้ใช้คำสั่ง apt-get install docker.io"
    }
  }
}
```

### With Title and Source
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "add_context",
    "arguments": {
      "content": "การแก้ปัญหา SSL certificate error: ให้ตรวจสอบ certificate expiry date และ update certificate ใหม่",
      "title": "SSL Certificate Troubleshooting",
      "source": "technical_support"
    }
  }
}
```

### With Full Metadata
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "add_context",
    "arguments": {
      "content": "ผู้ใช้รายงานปัญหา login ไม่ได้ แก้ไขโดยการ reset password และ clear browser cache",
      "title": "Login Issue Resolution",
      "source": "user_support",
      "metadata": {
        "conversation_id": "conv_123",
        "user_id": "user_456",
        "issue_type": "authentication",
        "resolution_time": "5 minutes",
        "status": "resolved"
      }
    }
  }
}
```

## Best Practices

### 1. ใช้ Title ที่มีความหมาย
```json
// ❌ ไม่ดี
"title": "Context 1"

// ✅ ดี
"title": "การแก้ปัญหา Database Connection Timeout"
```

### 2. ระบุ Source ให้ชัดเจน
```json
// ❌ ไม่ดี
"source": "data"

// ✅ ดี
"source": "chat_conversation"
"source": "api_response"
"source": "troubleshooting_session"
```

### 3. เพิ่ม Metadata ที่เป็นประโยชน์
```json
"metadata": {
  "conversation_id": "conv_123",
  "timestamp": "2026-02-01T10:30:00Z",
  "user_type": "premium",
  "issue_category": "technical",
  "resolution_status": "resolved"
}
```

### 4. เขียน Content ที่สมบูรณ์
```json
// ❌ ไม่ดี - ข้อมูลไม่ครบ
"content": "แก้แล้ว"

// ✅ ดี - มีรายละเอียดครบถ้วน
"content": "ผู้ใช้รายงานปัญหา API timeout เมื่อเรียกใช้ /api/users endpoint แก้ไขโดยการเพิ่ม timeout setting เป็น 30 วินาที และ optimize database query ผลลัพธ์คือ response time ลดลงเหลือ 2 วินาที"
```

## Integration Patterns

### 1. After Problem Resolution
```python
# หลังจากแก้ปัญหาให้ผู้ใช้แล้ว
await add_context(
    content=f"ปัญหา: {problem_description}\nวิธีแก้: {solution}\nผลลัพธ์: {result}",
    title=f"แก้ปัญหา: {problem_type}",
    source="problem_resolution",
    metadata={
        "problem_type": problem_type,
        "resolution_time": resolution_time,
        "user_satisfaction": satisfaction_score
    }
)
```

### 2. After Learning New Information
```python
# หลังจากได้ข้อมูลใหม่จาก API หรือแหล่งอื่น
await add_context(
    content=new_information,
    title="ข้อมูลใหม่: " + topic,
    source="external_api",
    metadata={
        "api_endpoint": endpoint_url,
        "fetch_time": datetime.now(),
        "data_freshness": "latest"
    }
)
```

### 3. Conversation Summary
```python
# สรุปการสนทนาที่สำคัญ
await add_context(
    content=conversation_summary,
    title="สรุปการสนทนา: " + main_topic,
    source="conversation_summary",
    metadata={
        "conversation_length": message_count,
        "main_topics": topics_discussed,
        "action_items": action_items
    }
)
```

## Testing

ใช้ script `test-add-context.sh` เพื่อทดสอบ tool:

```bash
./test-add-context.sh
```

## Error Handling

Tool จะ return error message ในกรณีต่อไปนี้:

1. **Empty Content**: เมื่อ content ว่างเปล่า
2. **Service Not Initialized**: เมื่อ embedding หรือ storage service ยังไม่พร้อม
3. **Processing Error**: เมื่อเกิดข้อผิดพลาดในการประมวลผล

## Performance Notes

- Content จะถูกแบ่งเป็น chunks ตาม text processor
- แต่ละ chunk จะถูกสร้าง embedding แยกกัน
- BM25 index จะถูกอัปเดตอัตโนมัติ (ถ้าเปิดใช้งาน)
- ข้อมูลจะถูกเก็บใน Qdrant vector database

## Security Considerations

- ตรวจสอบ content ก่อนเก็บเพื่อป้องกันข้อมูลที่ไม่เหมาะสม
- ใช้ metadata เพื่อระบุแหล่งที่มาและสิทธิ์การเข้าถึง
- พิจารณาการเข้ารหัสข้อมูลที่ sensitive