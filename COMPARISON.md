# การเปรียบเทียบ MCP Server for MSSQL — ทำไมตัวนี้ดีที่สุดสำหรับ execute query

เอกสารนี้อธิบายว่าทำไม **MSSQL MCP Server เวอร์ชัน v5 + Database Context** (ตัวที่อยู่ในโฟลเดอร์
[`mssql-mcp-server/`](./mssql-mcp-server)) จึงถูกเลือกว่าเป็นตัวที่ดีที่สุดสำหรับงาน execute query
เมื่อเทียบกับ MSSQL MCP server ตัวอื่น ๆ ในคลัง repo

## ผู้เข้าแข่งขัน (MSSQL MCP server ที่มีอยู่)

| ตัว | ที่มา (repo ต้นทาง) | MCP tools | แนวคิด |
|---|---|---|---|
| **A. v5 + Database Context** ✅ เลือกตัวนี้ | [`2026-customLangFlow-and-v5-mcpserver-for-mssql`](https://github.com/aekanun2020/2026-customLangFlow-and-v5-mcpserver-for-mssql) | `execute_query_tool`, `preview_table`, `get_database_info_tool`, `refresh_db_cache`, **`get_database_context`** | generic read query + รู้ schema/ความสัมพันธ์ทั้ง DB |
| B. v5 (base) | [`2025-langflow-mcp`](https://github.com/aekanun2020/2025-langflow-mcp) (`sse-mssqlmcp-v5`) | `execute_query_tool`, `preview_table`, `get_database_info_tool`, `refresh_db_cache` | generic read query |
| C. base | [`2025-n8n-mcp`](https://github.com/aekanun2020/2025-n8n-mcp) (`sse-mssqlmcp`) | เหมือน B | generic read query (ต้นแบบ) |
| D. writer | [`2026-n8n-mcp`](https://github.com/aekanun2020/2026-n8n-mcp) (`sse-mssqlmcp-writer`) | `insert_post`, `insert_comment`, `insert_analysis`, `query_recent_data`, `query_joined_data`, `truncate_all_tables` | เขียนข้อมูลแบบ fixed-schema (Facebook) — **ไม่มี generic execute_query** |

## ตารางเปรียบเทียบความสามารถ

| ความสามารถ | A. v5+context ✅ | B. v5 | C. base | D. writer |
|---|:---:|:---:|:---:|:---:|
| รัน T-SQL อะไรก็ได้ (generic `execute_query`) | ✅ | ✅ | ✅ | ❌ |
| `get_database_context` (schema + FK graph + คู่มือ T-SQL ในครั้งเดียว) | ✅ | ❌ | ❌ | ❌ |
| Cache schema | ✅ | ✅ | ✅ | — |
| Cache **relationship graph (FK)** | ✅ | ❌ | ❌ | — |
| preview table / database info | ✅ | ✅ | ✅ | บางส่วน |
| เขียนข้อมูล (insert) | ผ่าน raw SQL | ผ่าน raw SQL | ผ่าน raw SQL | ✅ (parameterized) |
| SSE transport + Docker | ✅ | ✅ | ✅ | ✅ |
| ผ่านการทดสอบ business questions จริง | ✅ | — | — | — |

## โค้ดแกนของ `execute_query` (เหมือนกันทุกตัว A/B/C)

ทุกตัวใช้ core เดียวกัน ซึ่งออกแบบมาดีอยู่แล้ว:

```python
def execute_query(query: str) -> Dict[str, Any]:
    conn = get_connection()
    if not conn:
        return {"error": "Could not connect to the database."}
    try:
        df = pd.read_sql(text(query), conn)          # ใช้ pandas จัดรูปผลลัพธ์อ่านง่าย
        if df.empty:
            return {"result": "Query executed successfully but returned no results."}
        result = df.to_string(index=False)
        if len(result) > 10000:                      # จำกัดขนาดผลลัพธ์
            result = df.head(100).to_string(index=False)
            result += f"\n\n[Showing only 100 of {len(df)} rows]"
        return {"result": result}
    except Exception as e:
        return {"error": f"Error executing query: {str(e)}"}
    finally:
        conn.close()
```

จุดเด่นของ core นี้: จัดการ connection ล้มเหลว, ผลลัพธ์ว่าง, error เป็น JSON และจำกัดขนาด output อัตโนมัติ

## จุดชี้ขาด: ทำไม A (v5+context) ชนะ

ในเมื่อ A, B, C ใช้ `execute_query` core เดียวกัน สิ่งที่ทำให้ **A ดีที่สุด** คือสิ่งที่ห่อรอบมัน:

### 1. tool `get_database_context` — ลด SQL error ที่ต้นเหตุ
A เพิ่ม tool พิเศษที่ให้ LLM agent เรียก **ก่อน** เขียน query เพื่อรับ:
- metadata ของฐานข้อมูล (ชื่อ, จำนวนตาราง, ขนาด)
- schema ทุกตาราง (คอลัมน์, ชนิด, nullability)
- **relationship graph (foreign keys + ตารางที่ไม่มีความสัมพันธ์)**
- คู่มือ T-SQL syntax + ตัวอย่าง query

ผลคือ agent เขียน JOIN และเลือกคอลัมน์ได้ถูกต้องตั้งแต่ครั้งแรก แทนที่จะลองผิดลองถูก B/C ไม่มี tool นี้
agent จึงต้องเดา schema เอง ทำให้เกิด SQL error ได้ง่ายกว่า

### 2. Cache relationship graph → เร็วและถูก
`DatabaseCache` ของ A เก็บ relationship graph เพิ่มจาก schema ธรรมดา ทำให้การเรียก
`get_database_context` ครั้งถัดไปเร็วมาก:

| การทำงาน | Cold cache | Warm cache |
|---|---|---|
| `get_database_context` | ~10 วินาที | **~23 ms** |

### 3. มีหลักฐานการทดสอบจริง
repo ต้นทางของ A ทดสอบกับคำถามธุรกิจจริงหลายระดับความยาก (Basic → Extreme):
- คะแนนเฉลี่ยสูงมาก (~98–99.5 / 100)
- **0 SQL error** — query รันสำเร็จทุกครั้ง
- ทำงานได้ดีเป็นพิเศษกับโมเดล `gpt-oss-120b` (เรียก context → preview → execute ครบขั้นตอน)

B, C, D ไม่มีชุดผลทดสอบเชิงประจักษ์แบบนี้

### 4. ทำไมไม่เลือก D (writer)
D ออกแบบมาสำหรับ "เขียน" ข้อมูลตาม schema ตายตัว (Facebook posts/comments/analyses) และ
**จงใจไม่มี generic `execute_query`** เพื่อความปลอดภัย จึงไม่เหมาะกับโจทย์ "execute query แบบยืดหยุ่น"
ถ้าต้องการให้ agent ถามอะไรก็ได้กับฐานข้อมูล

## ข้อควรระวังด้านความปลอดภัย (มีในทุกตัว A/B/C)

docstring เขียนว่า read-only / SELECT only แต่โค้ดที่บังคับถูก comment ทิ้งไว้ใน `mcp_server.py`:

```python
# if not query.lower().startswith('select'):
#     return json.dumps({"error": "Only SELECT queries are allowed for security reasons."})
```

แปลว่าจริง ๆ แล้วมันรัน INSERT / UPDATE / DELETE / DROP ได้ หากต้องการใช้ใน production แบบ read-only
**ให้เปิดบรรทัดเช็คนี้กลับมา** ในไฟล์ `mssql-mcp-server/app/mcp_server.py`

## สรุป

> **MSSQL MCP Server v5 + Database Context** คือตัวที่ดีที่สุดสำหรับ execute query
> เพราะใช้ execute core ที่แข็งแรงเหมือนตัวอื่น แต่เพิ่ม `get_database_context` + relationship-graph cache
> ที่ช่วยให้ agent เขียน SQL ถูกต้องตั้งแต่แรก (0 SQL error) เร็วขึ้นมาก (10s → 23ms) และมีหลักฐานทดสอบจริงรองรับ

---

แหล่งที่มา:
- [2026-customLangFlow-and-v5-mcpserver-for-mssql](https://github.com/aekanun2020/2026-customLangFlow-and-v5-mcpserver-for-mssql) (ตัวที่เลือก + ผลทดสอบใน `.kiro/NOTES.md`)
- [2025-langflow-mcp](https://github.com/aekanun2020/2025-langflow-mcp) (v5 base)
- [2025-n8n-mcp](https://github.com/aekanun2020/2025-n8n-mcp) (base)
- [2026-n8n-mcp](https://github.com/aekanun2020/2026-n8n-mcp) (writer)
