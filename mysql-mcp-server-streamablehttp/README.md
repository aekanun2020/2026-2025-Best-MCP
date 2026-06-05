# MySQL MCP Server (Streamable HTTP)

A [Model Context Protocol](https://modelcontextprotocol.io) server for **MySQL / MariaDB**, exposed over the **Streamable HTTP** transport (single `/mcp` endpoint, `application/json` responses). It runs in **stateless** mode so it works reliably with a wide range of agents/clients that don't perfectly implement the MCP session lifecycle.

This is a MySQL port of the MSSQL reference server
[`mssql-mcp-server-streamablehttp`](https://github.com/aekanun2020/2026-2025-Best-MCP/tree/main/mssql-mcp-server-streamablehttp).
Architecture and tool surface are identical; only the database layer and SQL dialect were adapted (T-SQL → MySQL, `pymssql` → `PyMySQL`, `sys.*` catalog → `INFORMATION_SCHEMA`).

> Design rationale (stateless vs stateful, spec details, client compatibility issues) is documented in
> [`MCP-Streamable-HTTP-Stateless-vs-Stateful.md`](./MCP-Streamable-HTTP-Stateless-vs-Stateful.md).

---

## Features

- **Streamable HTTP transport** — one endpoint (`/mcp`) handling `POST`, `GET`, `DELETE`.
- **Stateless** — every request is independent; an `Mcp-Session-Id` is minted on `initialize` for spec-compliant clients but is **not required** on later requests. Tolerant of buggy clients.
- **5 tools**, **2 resources**, **2 prompts** (see below).
- **Schema + relationship awareness** — discovers foreign keys and "loner" (standalone) tables, and ships a MySQL syntax guide to steer the LLM toward correct queries.
- **Unicode-safe** (`utf8mb4`) — handles Thai / emoji / multi-byte data.
- **Security** — `Origin` validation (DNS-rebinding protection), CORS config, non-root Docker user, optional read-only guard.

---

## Tools

| Tool | Description |
|---|---|
| `get_database_context` | **Call first.** Full DB context: schemas, FK relationships, loner tables, MySQL syntax guide, common queries. |
| `execute_query_tool` | Run an arbitrary MySQL query. Use for COUNT / SUM / WHERE / GROUP BY / JOIN / exact answers. |
| `preview_table` | Sample rows from a table (`SELECT * FROM \`t\` LIMIT n`). For eyeballing data only — not for aggregates. |
| `get_database_info_tool` | DB name, server, port, table count, version, size (MB). |
| `refresh_db_cache` | Reload cached table list / schemas / relationship graph after a schema change. |

### Resources

| URI | Description |
|---|---|
| `mysql://tables` | List all base tables. |
| `mysql://schema/{table_name}` | Column schema for one table. |

### Prompts

| Prompt | Description |
|---|---|
| `data_analysis_template` | Analysis template for a given table. |
| `generate_sql_query` | Generate a MySQL query from a natural-language description. |

---

## Configuration

Copy `.env.example` to `.env` and edit:

```env
DB_SERVER=host.docker.internal   # or 127.0.0.1 for local
DB_PORT=3306
DB_NAME=testdb
DB_USER=root
DB_PASSWORD=Passw0rd123456

HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
ALLOWED_ORIGINS=*                 # comma-separated list in production
```

---

## Run locally (Python)

```bash
./start_dev.sh
# or manually:
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # then edit
python main.py             # serves http://localhost:8000/mcp
```

## Run with Docker

```bash
./start_docker.sh                 # build + run (foreground)
# or full rebuild + automated test:
./rebuild_and_test.sh             # serves http://localhost:9000/mcp
```

`docker-compose.yml` maps host `9000` → container `8000` and adds a
`host.docker.internal` mapping so the container can reach a MySQL server
running on the host (works on Docker Desktop and Linux).

---

## Connect from a client

**Claude Desktop** (via `mcp-remote`, since Desktop speaks stdio):

```json
{
  "mcpServers": {
    "mysql-streamable-http": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:9000/mcp"]
    }
  }
}
```

Native Streamable HTTP clients can point directly at `http://localhost:9000/mcp`
(see `claude_desktop_config.json`).

---

## Testing

```bash
# Official MCP SDK client smoke test (server on :9000)
python test_client.py

# Full end-to-end protocol + tool suite (set MCP_BASE_URL to your server)
MCP_BASE_URL=http://127.0.0.1:8000 python test_all_tools.py
```

`test_all_tools.py` runs 16 checks covering the full lifecycle
(`initialize` → `notifications/initialized` → `tools/list` → every tool →
`resources/list` / `resources/read` → `GET` 405 → stateless no-session and
arbitrary-session acceptance → `DELETE` terminate) and writes
`test_results.json`. All 16 pass against a live MySQL/MariaDB.

---

## curl examples

Stateless — call a tool directly, no session id needed:

```bash
curl -i -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"get_database_info_tool","arguments":{}}}'
```

---

## Security notes

- Set `ALLOWED_ORIGINS` to your trusted origins in production (not `*`).
- Put authentication (Bearer / OAuth) in front of the server; `Mcp-Session-Id` is **not** a credential.
- To make the server read-only, uncomment the SELECT-only guard in
  `app/mcp_server.py` (`execute_query_tool`).
- Use HTTPS in production.

---

## Project layout

```
mysql-mcp-server-streamablehttp/
├── app/
│   ├── __init__.py
│   ├── database.py        # PyMySQL/SQLAlchemy engine, schema & relationship queries
│   └── mcp_server.py      # FastMCP tools/resources/prompts (MySQL dialect)
├── main.py                # FastAPI app + Streamable HTTP /mcp endpoint (stateless)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── test_client.py         # official MCP SDK client test
├── test_all_tools.py      # 16-check e2e suite
├── start_dev.sh / start_docker.sh / rebuild_and_test.sh
└── claude_desktop_config.json
```

---

## Differences from the MSSQL version

| Aspect | MSSQL | MySQL (this repo) |
|---|---|---|
| Driver | `pymssql` | `PyMySQL` |
| SQLAlchemy URL | `mssql+pymssql://` | `mysql+pymysql://...?charset=utf8mb4` |
| Row limit | `SELECT TOP n` | `LIMIT n` |
| Current time | `GETDATE()` | `NOW()` / `CURDATE()` |
| Identifier quote | `[brackets]` | `` `backticks` `` |
| Catalog for FKs | `sys.foreign_keys` | `INFORMATION_SCHEMA.KEY_COLUMN_USAGE` |
| DB size | `sys.database_files` | `SUM(data_length + index_length)` |
| Resource URIs | `mssql://...` | `mysql://...` |
