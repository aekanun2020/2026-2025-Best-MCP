# 2026-2025-Best-MCP

รวม **MCP server for MSSQL ที่ดีที่สุดสำหรับงาน execute query** ที่คัดเลือกมาจากการเปรียบเทียบ
MCP server หลายตัวในคลัง repo ของ [@aekanun2020](https://github.com/aekanun2020)

## ตัวที่เลือก

[`mssql-mcp-server/`](./mssql-mcp-server) — MSSQL MCP Server (SSE) เวอร์ชัน **v5 + Database Context**
นำมาจาก repo [`2026-customLangFlow-and-v5-mcpserver-for-mssql`](https://github.com/aekanun2020/2026-customLangFlow-and-v5-mcpserver-for-mssql)

เหตุผลที่เลือกตัวนี้ และตารางเปรียบเทียบกับตัวอื่น ดูได้ที่ [COMPARISON.md](./COMPARISON.md)

## สรุปสั้น ๆ ว่าทำไมตัวนี้ดีที่สุด

- มี tool `get_database_context` ที่ดึง schema + ความสัมพันธ์ (foreign keys) + คู่มือ T-SQL ของทั้ง DB ในครั้งเดียว ทำให้ LLM agent เขียน SQL ได้ถูกต้องก่อนยิง `execute_query_tool` → ลด SQL error
- มี `DatabaseCache` ที่ cache ทั้ง schema และ relationship graph ลดเวลา context จาก ~10 วินาที (cold) เหลือ ~23ms (warm)
- ผ่านการทดสอบจริงด้วยคำถามธุรกิจหลายระดับ ได้คะแนนเฉลี่ยสูง (~98–99.5/100) และ 0 SQL error
- รองรับ SSE transport + Docker + Claude Desktop config พร้อมใช้

## เริ่มใช้งาน

```bash
cd mssql-mcp-server
cp .env.example .env   # ตั้งค่า DB_SERVER / DB_NAME / DB_USER / DB_PASSWORD
docker-compose up      # server เปิดที่ http://localhost:9000/sse
```
