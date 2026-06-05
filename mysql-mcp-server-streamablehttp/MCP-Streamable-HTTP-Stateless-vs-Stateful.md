# MCP Streamable HTTP: Stateless vs Stateful — คู่มือฉบับสมบูรณ์

> เอกสารอ้างอิงสำหรับการสร้าง MCP server แบบ Streamable HTTP ที่รองรับทั้ง stateless และ stateful mode
> ให้เข้ากันได้กับ agent/client ทั่วไปอย่างมั่นใจ
>
> รวบรวมจาก: MCP Official Spec (2025-06-18), FastMCP/Python SDK, TypeScript SDK, และรายงานปัญหาจริงจากชุมชน
> อัปเดต: มิถุนายน 2026

---

## สารบัญ

1. [TL;DR — สรุปสำหรับคนรีบ](#1-tldr--สรุปสำหรับคนรีบ)
2. [พื้นฐาน Streamable HTTP](#2-พื้นฐาน-streamable-http)
3. [Stateful vs Stateless — ความต่างเชิงลึก](#3-stateful-vs-stateless--ความต่างเชิงลึก)
4. [Mcp-Session-Id และ Lifecycle ตาม Spec](#4-mcp-session-id-และ-lifecycle-ตาม-spec)
5. [ปัญหา Client จริงที่พบในสนาม](#5-ปัญหา-client-จริงที่พบในสนาม)
6. [การตัดสินใจ: เลือกโหมดไหน](#6-การตัดสินใจ-เลือกโหมดไหน)
7. [โค้ดตัวอย่าง: Python / FastMCP](#7-โค้ดตัวอย่าง-python--fastmcp)
8. [โค้ดตัวอย่าง: TypeScript SDK (dual-mode)](#8-โค้ดตัวอย่าง-typescript-sdk-dual-mode)
9. [Test Client](#9-test-client)
10. [Deployment & Scaling](#10-deployment--scaling)
11. [Security Checklist](#11-security-checklist)
12. [Troubleshooting](#12-troubleshooting)
13. [อนาคตของ MCP Transport](#13-อนาคตของ-mcp-transport)
14. [แหล่งอ้างอิง](#14-แหล่งอ้างอิง)

---

## 1. TL;DR — สรุปสำหรับคนรีบ

- **MCP ออกแบบมาให้เป็น stateful protocol โดยกำเนิด** — ต้องผ่าน initialization phase (handshake แลก capabilities) ก่อนคุยกัน
- **Streamable HTTP** ใช้ endpoint เดียว (เช่น `/mcp`) รองรับ POST + GET, upgrade เป็น SSE ได้เมื่อต้องการ stream/notification
- **Stateful** = server ออก `Mcp-Session-Id`, client ต้องแนบทุก request → ครอบคลุมฟีเจอร์ครบ แต่ต้อง sticky session / long-running server
- **Stateless** = ไม่มี session id, ทุก request อิสระ → scale ง่าย, serverless ได้, ทนต่อ client ที่ทำตาม spec ไม่ครบ แต่ใช้ฟีเจอร์ขั้นสูง (notification/sampling/subscription) ไม่ได้
- **"ชัวร์ที่สุดกับ agent ทั่วไป":**
  - ถ้า tool เป็นอิสระ ไม่ต้องจำ context → **stateless** (ทนต่อ buggy client ได้ดีสุด)
  - ถ้าต้องใช้ฟีเจอร์ขั้นสูง → **stateful** แต่ออกแบบให้ fallback ได้
  - **ทางที่ดีที่สุด: รองรับทั้ง 2 โหมดในโค้ดเดียว สลับด้วย flag/env** (เอกสารนี้มีตัวอย่างครบ)

---

## 2. พื้นฐาน Streamable HTTP

Streamable HTTP มาแทนที่ HTTP+SSE transport เดิม (deprecated ตั้งแต่ spec 2024-11-05) โดยรวมเป็น **endpoint เดียว**

### กลไกหลัก
| รายการ | รายละเอียด |
|---|---|
| HTTP methods | ใช้ทั้ง POST และ GET ที่ endpoint เดียวกัน |
| MCP endpoint | server **MUST** มี path เดียวที่รองรับทั้ง POST และ GET (เช่น `https://example.com/mcp`) |
| การส่งข้อความ | ทุก JSON-RPC message จาก client = HTTP POST ใหม่ 1 ครั้ง |
| Accept header | client **MUST** ส่ง `Accept: application/json, text/event-stream` |
| SSE upgrade | server เลือกตอบเป็น `application/json` (single response) หรือ `text/event-stream` (stream) ได้ |
| GET → SSE | client **MAY** ส่ง GET เพื่อเปิด SSE stream รับ server-initiated message โดยไม่ต้อง POST ก่อน |
| GET ไม่รองรับ SSE | ถ้า server ไม่เปิด SSE ที่ endpoint นี้ ต้องตอบ `405 Method Not Allowed` |
| Protocol version | หลัง init แล้ว client **MUST** ส่ง header `MCP-Protocol-Version: <version>` ทุก request (เช่น `2025-06-18`) |
| Default version | ถ้า server ไม่ได้รับ header นี้ → **SHOULD** สมมติว่าเป็น `2025-03-26` |
| Invalid version | ถ้าได้รับ version ที่ไม่รองรับ → **MUST** ตอบ `400 Bad Request` |

### ข้อดีของ Streamable HTTP เทียบ SSE เดิม
- **Two-way communication บน endpoint เดียว** ไม่ต้อง juggle 2 connection
- **Auth ง่ายขึ้น** — แนบ `Authorization: Bearer` ได้ทุก request (ไม่ใช่แค่ตอนเปิด connection)
- **Infrastructure-friendly** — วางหลัง AWS ALB / Cloudflare ได้, ใช้ CORS/auth middleware มาตรฐานได้
- **Stateless ได้** — แต่ละ POST เป็นอิสระ ทำให้ scale แนวนอนได้โดยไม่ต้อง sticky session (ในโหมด stateless)

---

## 3. Stateful vs Stateless — ความต่างเชิงลึก

| มิติ | Stateful | Stateless |
|---|---|---|
| Session ID | server ออก `Mcp-Session-Id` ตอน init, client แนบทุก request | ไม่มี session id, ทุก request อิสระ |
| State เก็บที่ไหน | ใน memory ของ server instance (หรือ external store) | ไม่เก็บ (หรือเก็บใน DB/Redis ถ้าจำเป็น) |
| Initialization | handshake จริงครั้งเดียว, reuse ได้ | ทุก request เหมือน init ใหม่ |
| รองรับหลาย client | แยกด้วย session id ได้ชัดเจน | ทุก request ต้อง isolate กันเอง (สร้าง transport/server ใหม่ต่อ request) |
| Server-initiated msg | ได้ (notification, sampling, logging) | **ไม่ได้** |
| Resource subscription | ได้ | ไม่ได้ |
| Tools list changed notification | ได้ | ไม่ได้ |
| Deployment | ต้อง sticky session / long-running (VPS) | scale แนวนอน, serverless (Vercel, Lambda) ได้ |
| ทนต่อ buggy client | ต่ำ — client ที่ไม่ส่ง session id จะพัง (400) | สูง — ignore session id ที่ client ส่งมาได้ |
| ความสอดคล้องกับ spec | ตรงตาม design ดั้งเดิมของ MCP | เป็นการ relax กฎ (ชุมชนถกเถียงว่า "ไม่ตรง spec แท้") |

### หัวใจของความต่าง
ใน Streamable HTTP **วิธีเดียวที่จะแยก client หลายตัวออกจากกันคือ session id** เพราะหลาย request วิ่งเข้า endpoint เดียวกัน
- มี session id → server รู้ว่า request นี้เป็นของ connection ไหน → รักษา context ได้
- ไม่มี session id → ทุก client เหมือนใช้ connection เดียวกัน → ถ้า server ต้องจำ state จะพัง

**Insight สำคัญ:** ถ้า server **ไม่จำเป็นต้องเก็บ context ข้ามคำสั่ง** (tool list คงที่, แต่ละ tool call อิสระ ไม่ต้องจำผลก่อนหน้า) → session id ไม่จำเป็นเลย และ stateless จะ robust กว่า

> หมายเหตุ: `Mcp-Session-Id` **ไม่ใช่ authentication** — auth เป็นหน้าที่ของ OAuth/Bearer token ต่างหาก session id มีไว้แยก connection + รักษา context เท่านั้น

---

## 4. Mcp-Session-Id และ Lifecycle ตาม Spec

อ้างอิง MCP Spec 2025-06-18 (Streamable HTTP transport, Session management):

| เหตุการณ์ | ข้อกำหนด |
|---|---|
| ออก session id | server **MAY** ออก `Mcp-Session-Id` ใน header ของ response ที่มี `InitializeResult` |
| รูปแบบ session id | **SHOULD** unique + cryptographically secure (UUID, JWT, hash); **MUST** เป็น visible ASCII (0x21–0x7E) เท่านั้น |
| client ต้องแนบ id | ถ้า server ออก id มา → client **MUST** แนบ `Mcp-Session-Id` ทุก request ถัดไป |
| request ไม่มี id | server ที่ require session **SHOULD** ตอบ `400 Bad Request` (ยกเว้น init) |
| terminate session | server **MAY** ปิด session ได้ทุกเมื่อ → หลังจากนั้น request ที่มี id เดิม **MUST** ได้ `404 Not Found` |
| client เจอ 404 | **MUST** เริ่ม session ใหม่ด้วย `InitializeRequest` (ไม่แนบ id เก่า) |
| client เลิกใช้ session | **SHOULD** ส่ง `HTTP DELETE` พร้อม `Mcp-Session-Id` เพื่อปิด session |
| server ไม่ให้ปิด | **MAY** ตอบ `405 Method Not Allowed` ต่อ DELETE |

### ลำดับ handshake (stateful)
```
1. POST /mcp   { jsonrpc:"2.0", method:"initialize", ... }
   ← 200 + header Mcp-Session-Id: <uuid>     (server มอบ id)

2. POST /mcp   method:"notifications/initialized"
   header: Mcp-Session-Id: <uuid>            (บอกว่า client พร้อมแล้ว)

3. POST /mcp   method:"tools/call", params:{...}
   header: Mcp-Session-Id: <uuid>            (เรียก tool จริง)
```
> ขั้นที่ 2 (`notifications/initialized`) สำคัญมาก — ถ้าข้าม server บางตัวจะถือว่า client ยังไม่พร้อมและปฏิเสธ tool call

### ลำดับ (stateless)
```
POST /mcp   method:"tools/call", params:{...}   ← ตอบกลับเลย ไม่ต้อง session id
```
ในโหมด stateless แม้ client จะส่ง `initialize` และพยายามเก็บ session id ก็ใช้งานได้ — server แค่ **ignore** session id นั้น

---

## 5. ปัญหา Client จริงที่พบในสนาม

เหตุผลที่ stateless "ชัวร์กว่า" ในแง่ความเข้ากันได้ คือมี client จริงหลายตัวที่จัดการ session id ไม่ตรง spec:

| Client / กรณี | อาการ | อ้างอิง |
|---|---|---|
| **continue.dev** | ส่ง request ออกผิดลำดับ / ก่อน init เสร็จ → server หา session id ไม่เจอ | Continue Issue #6006 |
| **Official TypeScript SDK** | `client.connect` เคย ignore `mcp-session-id` ที่ server ส่งมา | typescript-sdk Issue #852 |
| **TypeScript SDK (server)** | stateless mode พังก่อน v1.10.1 — `validateSession` fail เพราะไม่มี session id (`Bad Request: Server not initialized`) | typescript-sdk Issue #340 (แก้ใน 1.10.1) |
| **OpenAI connector** | สร้าง MCP session ใหม่ทุก invocation แทน reuse → state ไม่ต่อเนื่อง | OpenAI Community |
| **n8n (multi-instance)** | เก็บ session ใน memory; ถ้ารันหลาย worker request ตกที่ instance ที่ไม่มี session → error | n8n Community |

### บทเรียน
- อย่าหวังพึ่งว่า client ทุกตัวจะทำ lifecycle ครบ (init → initialized → ส่ง id ทุกครั้ง)
- ถ้า server เป็น stateful แต่ client ไม่ส่ง id กลับ → ตอบ `400` → **พัง**
- ถ้า server เป็น stateless → ignore id ที่ client ส่งมาได้ → **ไม่พัง**
- ระวัง version ของ SDK: ใช้ Python SDK ≥ 1.10.1 / FastMCP รุ่นใหม่ เพื่อให้ stateless ทำงานถูกต้อง

---

## 6. การตัดสินใจ: เลือกโหมดไหน

```
server ต้องเก็บ context ข้ามคำสั่งไหม?
(เช่น จำผลลัพธ์ก่อนหน้า, มี resource subscription, ส่ง notification หา client)
│
├─ ไม่ → tool เป็นอิสระล้วน
│        → STATELESS  (ชัวร์สุดกับ agent ทั่วไป, scale ง่าย, ทน buggy client)
│
└─ ใช่ → ต้องใช้ฟีเจอร์ขั้นสูง
         → STATEFUL
         │
         ├─ deploy instance เดียว / VPS → in-memory session พอ
         └─ deploy หลาย instance / serverless → STATEFUL + external store (Redis)
                                                + sticky session (ถ้ามี LB)
```

| สถานการณ์ | คำแนะนำ |
|---|---|
| Tools อิสระ (API wrapper, calculator, lookup) | **Stateless** |
| ต้อง notification / sampling / subscription | **Stateful** |
| ไม่แน่ใจ / อยากครอบคลุมสุด | **Stateful + Redis + fallback graceful** หรือ **รองรับ 2 โหมดด้วย flag** |
| ทดสอบกับ client หลากหลายให้กว้างสุดก่อน | เริ่มที่ **Stateful (default)** แล้วเพิ่ม stateless option |

**สำหรับเป้าหมาย "ใช้ได้กับ agent ทั่วไปอย่างแน่นอน":** ทำให้รองรับทั้ง 2 โหมด สลับด้วย env/flag ตามตัวอย่างด้านล่าง — ได้ทั้งความครอบคลุมและความยืดหยุ่น

---

## 7. โค้ดตัวอย่าง: Python / FastMCP

> ต้องใช้ `mcp` >= 1.10.1 (`pip install "mcp>=1.10.1"`)
> รุ่นต่ำกว่านี้มีบั๊ก stateless mode

### 7.1 Dual-mode ด้วย FastMCP (วิธีที่ง่ายที่สุด)

```python
# server.py
import os
from mcp.server.fastmcp import FastMCP

# เลือกโหมดจาก environment variable
# MCP_MODE=stateless  หรือ  MCP_MODE=stateful (default)
MODE = os.getenv("MCP_MODE", "stateful").lower()
STATELESS = MODE == "stateless"

# json_response=True : ตอบเป็น application/json ธรรมดา (ไม่เปิด SSE)
#   เหมาะกับ stateless + client ที่ไม่ต้องการ stream
mcp = FastMCP(
    "DualModeServer",
    host="127.0.0.1",          # bind localhost เท่านั้นเมื่อรัน local (ความปลอดภัย)
    port=int(os.getenv("PORT", "3000")),
    stateless_http=STATELESS,
    json_response=STATELESS,   # stateless มักคู่กับ json_response
)


@mcp.tool()
def add(a: int, b: int) -> int:
    """บวกเลขสองจำนวน"""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """คูณเลขสองจำนวน"""
    return a * b


if __name__ == "__main__":
    print(f"[startup] mode={'STATELESS' if STATELESS else 'STATEFUL'} "
          f"port={mcp.settings.port}")
    # transport = "streamable-http" คือ endpoint /mcp
    mcp.run(transport="streamable-http")
```

รันแบบ stateful (default):
```bash
python server.py
```
รันแบบ stateless:
```bash
MCP_MODE=stateless python server.py
```

### 7.2 สรุป flag ของ FastMCP

| Flag | ความหมาย |
|---|---|
| `stateless_http=False` (default) | Stateful — มี session, รองรับ SSE, notification |
| `stateless_http=True` | Stateless — ไม่มี session memory ระหว่าง request |
| `json_response=True` | ตอบเป็น `application/json` แทน SSE (เหมาะกับ stateless / client ที่ไม่ stream) |
| `transport="streamable-http"` | ใช้ Streamable HTTP transport (endpoint `/mcp`) |

> อ้างอิงจาก PyPI `mcp` 1.10.1:
> ```python
> mcp = FastMCP("StatefulServer")                                  # stateful
> mcp = FastMCP("StatelessServer", stateless_http=True)            # stateless
> mcp = FastMCP("StatelessServer", stateless_http=True, json_response=True)  # stateless + json
> ```

### 7.3 หมายเหตุ FastMCP 3.0
- State **persist ข้าม tool call ภายใน session** ได้ (ไม่ใช่แค่ภายใน request เดียว) และถูก key ด้วย session id อัตโนมัติ → isolate ระหว่าง client
- โหมด Stateless HTTP: FastMCP เคารพ header `mcp-session-id` ที่ client ส่งมา; ถ้าตั้ง storage backend ไว้ จะสร้าง "virtual session" ให้
- `Context.transport` property บอกได้ว่ากำลังใช้ transport อะไร (`"stdio"`, `"sse"`, `"streamable-http"`)

---

## 8. โค้ดตัวอย่าง: TypeScript SDK (dual-mode)

> ต้องใช้ `@modelcontextprotocol/sdk` >= 1.10.1 (stateless ก่อนหน้านี้พัง — Issue #340)
> `npm i @modelcontextprotocol/sdk express`

ตัวอย่างนี้รองรับ **ทั้ง stateful และ stateless ในไฟล์เดียว** สลับด้วย env `MCP_MODE`:

```typescript
// server.ts
import express, { Request, Response } from "express";
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

const STATELESS = (process.env.MCP_MODE ?? "stateful").toLowerCase() === "stateless";
const PORT = Number(process.env.PORT ?? 3000);

// ---- factory: สร้าง McpServer ใหม่พร้อม tools ----
function buildServer(): McpServer {
  const server = new McpServer({ name: "dual-mode-server", version: "1.0.0" });

  server.tool(
    "add",
    { a: z.number(), b: z.number() },
    async ({ a, b }) => ({ content: [{ type: "text", text: String(a + b) }] })
  );

  server.tool(
    "multiply",
    { a: z.number(), b: z.number() },
    async ({ a, b }) => ({ content: [{ type: "text", text: String(a * b) }] })
  );

  return server;
}

const app = express();
app.use(express.json());

// ================= STATELESS =================
// สร้าง transport + server ใหม่ทุก request เพื่อ isolate กันสมบูรณ์
// (ใช้ instance เดียวร่วมกันจะทำให้ request id ชนกันเมื่อหลาย client เข้าพร้อมกัน)
if (STATELESS) {
  app.post("/mcp", async (req: Request, res: Response) => {
    try {
      const server = buildServer();
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined, // <-- undefined = stateless
      });
      res.on("close", () => {
        transport.close();
        server.close();
      });
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    } catch (err) {
      console.error("MCP error:", err);
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal server error" },
          id: null,
        });
      }
    }
  });

  // stateless ไม่รองรับ GET/DELETE → ตอบ 405
  const methodNotAllowed = (_req: Request, res: Response) =>
    res.writeHead(405).end(
      JSON.stringify({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed." },
        id: null,
      })
    );
  app.get("/mcp", methodNotAllowed);
  app.delete("/mcp", methodNotAllowed);
}

// ================= STATEFUL =================
else {
  // เก็บ transport ตาม session id
  const transports: Record<string, StreamableHTTPServerTransport> = {};

  app.post("/mcp", async (req: Request, res: Response) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    let transport: StreamableHTTPServerTransport;

    if (sessionId && transports[sessionId]) {
      // reuse session เดิม
      transport = transports[sessionId];
    } else if (!sessionId && isInitializeRequest(req.body)) {
      // init ใหม่
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        onsessioninitialized: (sid) => {
          transports[sid] = transport;
        },
      });
      transport.onclose = () => {
        if (transport.sessionId) delete transports[transport.sessionId];
      };
      const server = buildServer();
      await server.connect(transport);
    } else {
      // ไม่มี session id และไม่ใช่ init → ปฏิเสธ
      res.status(400).json({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Bad Request: No valid session ID provided" },
        id: null,
      });
      return;
    }
    await transport.handleRequest(req, res, req.body);
  });

  // GET (SSE stream) และ DELETE (terminate) ใช้ handler ร่วมกัน
  const handleSessionRequest = async (req: Request, res: Response) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    if (!sessionId || !transports[sessionId]) {
      res.status(400).send("Invalid or missing session ID");
      return;
    }
    await transports[sessionId].handleRequest(req, res);
  };
  app.get("/mcp", handleSessionRequest);
  app.delete("/mcp", handleSessionRequest);
}

app.listen(PORT, () => {
  console.log(
    `MCP ${STATELESS ? "STATELESS" : "STATEFUL"} server on http://127.0.0.1:${PORT}/mcp`
  );
});
```

รัน:
```bash
# stateful (default)
npx tsx server.ts
# stateless
MCP_MODE=stateless npx tsx server.ts
```

### จุดสำคัญของโค้ด TS
- **Stateless:** `sessionIdGenerator: undefined` + สร้าง transport/server ใหม่ทุก request (กัน request id ชนกัน)
- **Stateful:** `sessionIdGenerator: () => randomUUID()` + เก็บใน dict + เช็ค `isInitializeRequest`
- **เงื่อนไขสร้าง session ใหม่:** ต้อง (ไม่มี session เดิม) **และ** (เป็น init request) พร้อมกันเท่านั้น

---

## 9. Test Client

### 9.1 ทดสอบด้วย curl (เห็น header ชัด)

Stateful — ขอ session id ก่อน:
```bash
# 1) initialize → ดู header Mcp-Session-Id ใน response
curl -i -X POST http://127.0.0.1:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'

# 2) ใช้ session id ที่ได้ (สมมติ <SID>) ส่ง initialized
curl -i -X POST http://127.0.0.1:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <SID>" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# 3) เรียก tool
curl -i -X POST http://127.0.0.1:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <SID>" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"add","arguments":{"a":2,"b":3}}}'
```

Stateless — ยิงตรงได้เลย:
```bash
curl -i -X POST http://127.0.0.1:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"add","arguments":{"a":2,"b":3}}}'
```

### 9.2 Test client ด้วย Python SDK

```python
# test_client.py
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://127.0.0.1:3000/mcp"
    # streamablehttp_client จัดการ session id ให้อัตโนมัติ (ถ้า server ออกมา)
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])
            result = await session.call_tool("add", {"a": 2, "b": 3})
            print("add(2,3) =", result.content[0].text)


asyncio.run(main())
```
```bash
python test_client.py    # ใช้ได้ทั้ง server stateful และ stateless
```

### 9.3 เชื่อมกับ Claude Desktop (ผ่าน mcp-remote)
Claude Desktop ยังพูด stdio เป็นหลัก ใช้ `mcp-remote` เป็นสะพานไป streamable HTTP:
```json
{
  "mcpServers": {
    "dual-mode": {
      "command": "npx",
      "args": ["mcp-remote", "http://127.0.0.1:3000/mcp"]
    }
  }
}
```

---

## 10. Deployment & Scaling

| โหมด | Deploy ได้ที่ไหน | ต้องทำอะไรเพิ่ม |
|---|---|---|
| Stateless | Vercel, AWS Lambda, Cloud Run, container หลาย replica | ไม่ต้อง — scale แนวนอนได้เลย |
| Stateful (1 instance) | VPS, single container, long-running process | ไม่ต้อง — in-memory พอ |
| Stateful (หลาย instance) | K8s, ECS, หลาย replica | **sticky session** ที่ LB **หรือ** external store (Redis) |

### Stateful แบบ scale ได้ → เก็บ state ใน Redis
- เก็บ transport/session info ใน Redis แทน memory → server แต่ละ node ดึง session เดียวกันได้ → ไม่ต้อง sticky session
- มีค่า overhead เพิ่ม แต่แลกกับ horizontal scaling
- reference: `mcp-on-vercel` (ออกแบบสำหรับ Vercel, ปรับใช้กับ serverless platform อื่นได้)

### ข้อควรระวังกับ proxy (nginx / traefik)
ถ้าใช้ SSE (stateful) ผ่าน proxy:
- ปิด gzip compression สำหรับ SSE
- ปิด proxy buffering สำหรับ SSE
- ตั้ง timeout ให้ยาวพอสำหรับ long-lived connection

---

## 11. Security Checklist

spec บังคับไม่ว่าจะโหมดไหน:

- [ ] **Validate `Origin` header** ทุก incoming connection (กัน DNS rebinding attack)
- [ ] **Bind localhost (127.0.0.1)** เมื่อรัน local — อย่า bind `0.0.0.0`
- [ ] **ทำ authentication** ทุก connection (OAuth / Bearer token)
- [ ] แยก **auth (OAuth/Bearer)** ออกจาก **session id** — session id ไม่ใช่ credential
- [ ] ตรวจ `MCP-Protocol-Version` header → ถ้าไม่รองรับตอบ `400`
- [ ] ใช้ HTTPS ใน production
- [ ] ตั้ง CORS policy ให้รัดกุม (เปิดเฉพาะ origin ที่ไว้ใจ)
- [ ] Session id ต้อง cryptographically secure (UUID/JWT/hash) และเป็น ASCII 0x21–0x7E

---

## 12. Troubleshooting

| อาการ | สาเหตุที่เป็นไปได้ | วิธีแก้ |
|---|---|---|
| `400 Bad Request: Server not initialized` (stateless) | ใช้ SDK เก่ากว่า 1.10.1 | อัปเดต SDK ≥ 1.10.1 |
| `400 Bad Request` (stateful) | client ไม่ส่ง `Mcp-Session-Id` กลับมา | ตรวจ client lifecycle / เปลี่ยนเป็น stateless |
| `404 Not Found` ระหว่างใช้งาน | server terminate session ไปแล้ว | client ต้อง init ใหม่ (ไม่แนบ id เก่า) |
| tool call ถูกปฏิเสธหลัง init | ข้ามขั้น `notifications/initialized` | ส่ง initialized notification ก่อนเรียก tool |
| หลาย client error เป็นช่วงๆ (multi-instance) | session อยู่คนละ instance | sticky session หรือ Redis store |
| request id ชนกัน (stateless) | ใช้ transport instance เดียวร่วมกัน | สร้าง transport/server ใหม่ทุก request |
| `405 Method Not Allowed` ตอน GET | server ไม่เปิด SSE ที่ endpoint นี้ | ปกติสำหรับ stateless/json_response — ไม่ใช่บั๊ก |

---

## 13. อนาคตของ MCP Transport

ทีม MCP กำลังวางโรดแมปให้ **โปรโตคอลเป็น stateless มากขึ้น**:
- แนวคิด: "agentic application เป็น stateful ได้ แต่ตัวโปรโตคอลไม่จำเป็นต้องเป็น" — เหมือน HTTP ที่ stateless ส่วน app ใช้ cookie/token สร้าง state เอง
- เป้าหมาย: scale ง่าย, serverless ได้, ไม่ต้อง sticky session / distributed store
- กำลัง standardize นิยาม "stateless" ให้ตรงกันทุก SDK
- ออกแบบ elicitation ให้ทำงานคล้าย chat API (ส่ง request+response กลับมาด้วยกัน) เพื่อลดการเก็บ state ฝั่ง server
- พิจารณาเพิ่ม TTL/ETag ให้ data เพื่อให้ client cache เองได้ → notification กลายเป็น optimization ไม่ใช่ requirement
- expose routing info (RPC method/tool name) ผ่าน HTTP path/header เพื่อให้ LB route ได้โดยไม่ต้อง parse JSON

**MCP จะรองรับแค่ 2 transport ทางการต่อไป:** STDIO (local) และ Streamable HTTP (remote) — เพื่อให้ทุก client/server interoperate กันได้ และให้ความสำคัญกับ backwards compatibility

> นัยต่อการตัดสินใจ: ทิศทางระยะยาวคือ stateless ดังนั้นถ้าออกแบบ server ใหม่และไม่ต้องใช้ฟีเจอร์ stateful จริงๆ การเลือก stateless ตั้งแต่แรกจะสอดคล้องกับอนาคต

---

## 14. Prompt Template สำหรับสั่งงานคราวหน้า

> ก๊อปหัวข้อนี้ไปวางในแชต พร้อมแนบไฟล์ .md นี้ แล้วเติมช่องว่าง — ผมจะได้ context ครบในครั้งเดียว ลดโอกาสผิดให้น้อยที่สุด

### 14.1 ข้อมูลที่ผมต้องรู้ก่อนเขียนโค้ด (ยิ่งครบ ยิ่งชัวร์)

| หัวข้อ | ทำไมต้องรู้ | ตัวอย่างคำตอบ |
|---|---|---|
| **ภาษา + SDK version** | API เปลี่ยนตามเวอร์ชัน (signature, import path) | Python `mcp==1.x.x` / TypeScript SDK `1.x.x` |
| **โหมดที่ต้องการ** | กำหนดสถาปัตยกรรม | stateless / stateful / รองรับทั้งคู่ |
| **Tools ที่ต้องการ** | กำหนด schema + logic | query MSSQL, เรียก REST API, อ่านไฟล์ ฯลฯ |
| **Data backend** | กำหนด driver/connection | MSSQL (pyodbc/pymssql), Postgres, REST, ไม่มี |
| **Auth** | กำหนด middleware | ไม่มี / Bearer token / OAuth |
| **Deploy target** | กำหนดว่าต้อง stateless ไหม | local / VPS / Docker / serverless (Vercel, Lambda) |
| **Config style** | ให้ตรงกับนิสัยคุณ | `.env` + conda, docker-compose |
| **ต้องรันทดสอบใน sandbox ก่อนส่งไหม** | พิสูจน์ว่า "ไม่ผิด" จริง | ใช่ (แนะนำ) / ไม่ต้อง |

### 14.2 Template พร้อมก๊อป (เติมในวงเล็บ)

```
จากไฟล์ MCP-Streamable-HTTP-Stateless-vs-Stateful.md ที่แนบมา
ช่วยสร้าง MCP server แบบ Streamable HTTP ให้ผม โดย:

- ภาษา/SDK: (Python mcp 1.x.x / TypeScript SDK 1.x.x)
- โหมด: (รองรับทั้ง stateless + stateful สลับด้วย env / เลือกอย่างใดอย่างหนึ่ง)
- Tools ที่ต้องการ:
  1. (ชื่อ tool — ทำอะไร — input/output)
  2. ...
- Data backend: (เช่น MSSQL ผ่าน pyodbc, connection string อยู่ใน .env)
- Auth: (ไม่มี / Bearer / OAuth)
- Deploy target: (local / Docker / serverless)
- Config: (.env + conda / docker-compose)

ข้อกำหนดสำคัญ:
- เช็คเวอร์ชัน SDK จริงในเครื่อง/ sandbox ก่อนเขียน แล้วปรับ syntax ให้ตรง
- รันทดสอบใน sandbox จริง: ติดตั้ง dependency + ยิง tool call ทั้ง 2 โหมด ให้ผ่านก่อนส่ง
- ทำตาม security checklist (validate Origin, bind 127.0.0.1, auth)
- ส่ง log การรันมาให้ดูด้วย
```

### 14.3 สิ่งที่ผมจะทำให้อัตโนมัติเมื่อได้รับงาน (เพื่อความ "ไม่ผิด")

1. **เช็คเวอร์ชัน SDK จริง** ใน sandbox (`pip show mcp` / `npm ls @modelcontextprotocol/sdk`) แล้วปรับ syntax ให้ตรงเวอร์ชันนั้น — ไม่ยึดตามตัวอย่างในไฟล์นี้ตายตัว
2. **เขียน server + test client** ลง sandbox
3. **รันจริง**: ติดตั้ง dependency → สตาร์ท server → ยิง `initialize` / `tools/call` ทั้ง stateful และ stateless → ตรวจผลลัพธ์
4. **แก้จนผ่าน** ก่อนส่ง — ไม่ส่งโค้ดที่ยังไม่ได้รัน
5. **ส่งโค้ด + log การรัน + วิธี deploy** ให้คุณ

> สรุป: ไฟล์นี้ทำให้ "สถาปัตยกรรมและการตัดสินใจไม่ผิด" ส่วน "โค้ดรันได้จริงไม่ผิด" มาจากการรันทดสอบใน sandbox ก่อนส่ง — สองอย่างนี้รวมกันคือความมั่นใจที่พิสูจน์ได้

---

## 15. แหล่งอ้างอิง

- [MCP Spec 2025-06-18 — Transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [MCP Spec 2025-03-26 — Transports (backwards compat)](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [Exploring the Future of MCP Transports — roadmap ทางการ](https://modelcontextprotocol.info/blog/transport-future/)
- [State, and long-lived vs short-lived connections — GitHub Discussion #102](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/102)
- [Streamable HTTP and optional sessions — Reddit r/mcp](https://www.reddit.com/r/mcp/comments/1mg88mh/streamable_http_and_optional_sessions/)
- [Why MCP's Move Away from SSE Simplifies Security — Auth0](https://auth0.com/blog/mcp-streamable-http/)
- [The Problem With MCP: Stateful Servers — AI Hero (Matt Pocock)](https://www.aihero.dev/the-problem-with-mcp-stateful-server)
- [MCP Python SDK — PyPI 1.10.1 (stateless_http, json_response)](https://pypi.org/project/mcp/1.10.1/)
- [MCP Python SDK — GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [What's New in FastMCP 3.0](https://www.jlowin.dev/blog/fastmcp-3-whats-new)
- [FastMCP — HTTP Deployment docs](https://gofastmcp.com/deployment/http)
- [TypeScript SDK Issue #340 — stateless mode fix (1.10.1)](https://github.com/modelcontextprotocol/typescript-sdk/issues/340)
- [TypeScript SDK Issue #852 — client ignores mcp-session-id](https://github.com/modelcontextprotocol/typescript-sdk/issues/852)
- [Continue Issue #6006 — missing session ID / out-of-order requests](https://github.com/continuedev/continue/issues/6006)
- [OpenAI Community — connector creates fresh session each invocation](https://community.openai.com/t/connector-tool-calls-generating-fresh-mcp-session-each-invocation/1364975)
- [n8n Community — MCP Client/Trigger nodes session handling](https://community.n8n.io/t/we-re-adding-mcp-client-tool-mcp-trigger-nodes-try-them-now/99338)
- [CodeSignal — Managing Stateful MCP Server Sessions](https://codesignal.com/learn/courses/developing-and-integrating-an-mcp-server-in-typescript/lessons/stateful-mcp-server-sessions)
- [YouTube — Stateless MCP Servers with Streamable HTTP](https://www.youtube.com/watch?v=PYMEspZPcmc)

---

*สร้างโดย Perplexity Computer — เก็บไฟล์นี้ไว้แล้วนำมาแนบเป็น context เพื่อสั่งงานต่อได้โดยไม่ต้องค้นซ้ำ*
