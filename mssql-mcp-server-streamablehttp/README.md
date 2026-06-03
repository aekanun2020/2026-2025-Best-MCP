# MSSQL MCP Server with Streamable HTTP Transport

MCP server สำหรับเข้าถึงฐานข้อมูล Microsoft SQL Server ผ่าน **Streamable HTTP transport** (มาตรฐาน MCP ปัจจุบัน ใช้ endpoint เดียว แทน HTTP+SSE แบบเก่า) รันเป็น container ด้วย Docker

## Features

- **Streamable HTTP Transport** — ใช้ endpoint เดียว (`/mcp`) รับ POST/GET/DELETE ตามมาตรฐาน MCP ปัจจุบัน
- **Stateless** — ไม่บังคับ `Mcp-Session-Id` (คล้าย FastMCP `stateless_http=True`) ต่อ client ได้หลากหลาย
- **MSSQL Integration** — เชื่อมต่อฐานข้อมูล Microsoft SQL Server
- **FastAPI + Uvicorn backend** — web framework ที่เร็วและทันสมัย
- **Docker Support** — รันเป็น container ได้ทั้งหมด

### MCP Tools (5)

| Tool | หน้าที่ |
|------|--------|
| `get_database_context` | ดึง context ของฐานข้อมูลทั้งหมด (schema, ความสัมพันธ์, คู่มือ T-SQL) — **ควรเรียกตัวนี้ก่อนรัน query** |
| `execute_query_tool` | รันคำสั่ง T-SQL query บนฐานข้อมูล |
| `preview_table` | ดูตัวอย่างข้อมูลในตาราง (กำหนดจำนวนแถวได้) |
| `get_database_info_tool` | ข้อมูลทั่วไปของฐานข้อมูล (ชื่อ, จำนวนตาราง, ขนาด, version) |
| `refresh_db_cache` | รีเฟรช cache ของ schema ฐานข้อมูล |

### MCP Resources (2)

| URI | หน้าที่ |
|-----|--------|
| `mssql://tables` | ลิสต์ตารางทั้งหมดในฐานข้อมูล |
| `mssql://schema/{table_name}` | ดึง schema ของตารางที่ระบุ |

## Installation

> **Prerequisites:** ติดตั้งและเปิด **Docker Desktop** ก่อน ([Mac](https://docs.docker.com/desktop/install/mac-install/) / [Windows](https://docs.docker.com/desktop/install/windows-install/)) ตรวจให้แน่ใจว่า SQL Server รันอยู่บนเครื่อง host ที่ port **1433** และ port **9000** บนเครื่องว่าง

ขั้นตอน Windows กับ Mac ต่างกันเล็กน้อย ทำตามหัวข้อของ OS ตัวเอง

---

### Windows (double-click)

**1. ดาวน์โหลดโปรเจกต์จาก GitHub**

เปิด `Command Prompt` (CMD) แล้วรัน:

```cmd
git clone https://github.com/aekanun2020/2026-2025-Best-MCP.git
cd 2026-2025-Best-MCP\mssql-mcp-server-streamablehttp
```

(ไม่มี Git? กดปุ่มสีเขียว **Code ▾** ที่ [หน้า repo](https://github.com/aekanun2020/2026-2025-Best-MCP) → **Download ZIP** → แตกไฟล์ → เปิดโฟลเดอร์ `mssql-mcp-server-streamablehttp`)

**2. เริ่มรัน server**

เปิดโฟลเดอร์ `mssql-mcp-server-streamablehttp` ใน File Explorer แล้ว **double-click ไฟล์ `start_docker.bat`**

หน้าต่าง CMD จะเปิดขึ้นมาและทำให้ทั้งหมดให้อัตโนมัติ:
- สร้าง `.env` จาก `.env.example` (ถ้ายังไม่มี)
- build Docker image
- รัน container และแสดง log สด

**3. เสร็จ**

เมื่อเห็น log ขึ้น health แล้ว server จะรันที่ **http://localhost:9000/mcp**
เปิดหน้าต่าง CMD ค้างไว้ — **ปิดหน้าต่าง = server หยุด** ถ้าจะหยุดให้ปิดหน้าต่างหรือกด `Ctrl + C`

---

### Mac (Terminal)

**1. ดาวน์โหลดโปรเจกต์จาก GitHub**

เปิด `Terminal` แล้วรัน:

```bash
git clone https://github.com/aekanun2020/2026-2025-Best-MCP.git
cd 2026-2025-Best-MCP/mssql-mcp-server-streamablehttp
```

**2. เริ่มรัน server**

```bash
chmod +x start_docker.sh   # ทำแค่ครั้งแรกครั้งเดียว
./start_docker.sh
```

script จะสร้าง `.env` จาก `.env.example` (ถ้ายังไม่มี), build image, รัน container และแสดง log สด

**3. เสร็จ**

เมื่อเห็น log ขึ้น health แล้ว server จะรันที่ **http://localhost:9000/mcp**
เปิด Terminal ค้างไว้ — ปิดหน้าต่าง (หรือกด `Ctrl + C`) = server หยุด

---

### Database configuration

ตัวติดตั้งจะ copy [`.env.example`](.env.example) ไปเป็น `.env` ให้อัตโนมัติ โดยตั้งค่าไว้สำหรับ SQL Server ที่รันบน**เครื่องเดียวกัน**กับ Docker Desktop:

```env
DB_SERVER=host.docker.internal
DB_NAME=TestDB
DB_USER=SA
DB_PASSWORD=Passw0rd123456
```

`host.docker.internal` ช่วยให้ container เข้าถึง SQL Server บนเครื่อง host ได้ ถ้าฐานข้อมูลอยู่ที่อื่น ให้แก้ `.env` (แล้วรัน start script ใหม่) เปลี่ยน `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` ให้ตรง

## Managing the container

ชื่อ container คือ **`mssql-mcp-streamable-http`** — รันคำสั่งเหล่านี้จากในโฟลเดอร์ `mssql-mcp-server-streamablehttp`

```bash
# เช็คสถานะ / health
docker ps

# ดู log สด
docker logs -f mssql-mcp-streamable-http

# หยุด server (เก็บ container ไว้ start ใหม่ได้)
docker compose stop

# เปิดใช้งานใหม่ภายหลัง
docker compose start
```

## Re-running with a new configuration

ถ้าแก้ `.env` (เช่น เปลี่ยน `DB_SERVER` หรือ password) ให้ apply config ใหม่ด้วยการ **rebuild + recreate** container ในที่เดิม:

```bash
docker compose up -d --build --force-recreate
```

> **ห้ามรัน `docker compose down`** — `down` จะลบ container พร้อม network (และอาจกระทบ resource อื่น) ซึ่งไม่จำเป็น
> คำสั่ง `up -d --build --force-recreate` จะ recreate container ในที่พร้อม `.env`/config ใหม่ให้อยู่แล้ว — ใช้แค่คำสั่งนี้คำสั่งเดียว

## API Endpoints

`/mcp` เป็น endpoint เดียวของ Streamable HTTP รองรับ 3 method:

| Method / Path | หน้าที่ |
|---------------|--------|
| `POST /mcp` | รับ JSON-RPC message ของ MCP (ตัวหลักที่ใช้สื่อสาร) |
| `GET /mcp` | เปิด SSE stream — server นี้ไม่มี server-initiated stream จึงคืน **405** ตาม spec |
| `DELETE /mcp` | ปิด session — โหมด stateless เป็น no-op คืน **200** เสมอ |
| `GET /health` | Health check (ใช้โดย Docker healthcheck) |
| `GET /` | ข้อมูล service และรายการ endpoint |

### Session handling (stateless)

Server ทำงานแบบ **stateless** (คล้าย FastMCP `stateless_http=True`):
ตอน `initialize` จะ mint `Mcp-Session-Id` ส่งกลับมาใน response header ไว้ให้ client ที่ต้องการใช้ (optional)
แต่ request ถัดไปจะถูกยอมรับ **ทั้งที่มีและไม่มี** header นี้
ทำให้ client ที่ไม่ได้ส่ง session id กลับมา (เช่น Streamable HTTP path ของ PyClaw) ต่อได้โดยไม่ต้องแก้อะไร

> **Note:** บน Docker server รันภายในที่ port **8000** แต่ expose ออกมาภายนอกที่ port **9000**

## MCP Client Configuration

สำหรับ Claude Desktop หรือ MCP client อื่นๆ ให้ต่อผ่าน `mcp-remote` (มันทำหน้าที่ bridge จาก Streamable HTTP server ไปเป็น stdio ที่ client เหล่านี้ต้องการ):

```json
{
  "mcpServers": {
    "mssql-streamable-http": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:9000/mcp",
        "--allow-http"
      ]
    }
  }
}
```

ถ้า client อยู่คนละเครื่องกับ server ให้เปลี่ยน `localhost` เป็น IP ของ server (เช่น LAN หรือ Tailscale address) ส่วน `--allow-http` จำเป็นเพราะ server เสิร์ฟผ่าน HTTP ธรรมดา ไม่ใช่ HTTPS

## License

MIT
