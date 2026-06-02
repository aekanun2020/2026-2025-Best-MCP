# Live Tool Test Report — Streamable HTTP MCP Server

End-to-end test of **every** tool, resource, prompt and protocol behaviour of the
`mssql-mcp-server-streamablehttp` server, executed against a **live SQL Server 2022**
database (`TestDB`, 1,432,440 rows in `loans_fact`) reached through a Cloudflare tunnel.

- **Endpoint tested:** `POST http://127.0.0.1:8044/mcp` (MCP Streamable HTTP)
- **Transport:** Streamable HTTP (single `/mcp` endpoint, `Mcp-Session-Id` header lifecycle)
- **Date:** 2026-06-02
- **Result:** **18 / 18 checks PASSED** ✅

## Screen captures

| File | Contents |
|------|----------|
| `01_init_and_tools.png` | initialize, notifications/initialized, tools/list, and all 5 tools |
| `02_resources_protocol_prompts.png` | resources/list+read, protocol checks (GET/no-session/bad-session/DELETE), prompts |
| `03_docker_container_run.png` | **Docker run via `./start_docker.sh`** — build, container health, and full 16/16 test against the running container |

## Docker deployment test (`./start_docker.sh`)

The server was also built and run as a **Docker container** exactly as the install manual
prescribes (`./start_docker.sh` → `docker compose build --no-cache` → `docker compose up`),
then the full test suite was fired at the running container.

- **Image:** `mssql-mcp-server-streamablehttp-mcp-server:latest` (375 MB, python:3.11-slim, non-root `mcpuser`)
- **Container:** `mssql-mcp-streamable-http`, status **healthy** (healthcheck on `/health`)
- **Port:** container `8000` exposed on host; manual specifies `9000:8000`. In the test sandbox host port 9000 was already occupied by a system process, so the container was published on `9001:8000` for the external test. The internal port and all app behaviour are unchanged.
- **DB connectivity:** container reached the live SQL Server through the host gateway → Cloudflare tunnel (`DB_SERVER=172.17.0.1:14333`); cache refresh found 6 tables.
- **Result:** **16 / 16 checks PASSED** against the container (see `03_docker_container_run.png`).

## What was tested

### Session lifecycle / protocol
| # | Check | Expected | Result |
|---|-------|----------|--------|
| 1 | `initialize` | 200 + `Mcp-Session-Id` returned | PASS |
| 2 | `notifications/initialized` | 202, empty body | PASS |
| 13 | `GET /mcp` | 405 (no server-initiated stream) | PASS |
| 14 | request with **no** session header | 400 "Missing Mcp-Session-Id header" | PASS |
| 15 | request with **bad** session | 404 "Session not found" | PASS |
| 16 | `DELETE /mcp` | 200 (session terminated) | PASS |

### Tools (5)
| # | Tool | Test | Result |
|---|------|------|--------|
| 3 | `tools/list` | returns exactly 5 tools | PASS |
| 4 | `get_database_info_tool` | DB name/size/version | PASS (TestDB, 464 MB, SQL Server 2022 RTM-CU24) |
| 5 | `refresh_db_cache` | refresh schema cache | PASS (6 tables) |
| 6 | `get_database_context` | full schema + T-SQL guide | PASS |
| 7 | `execute_query_tool` | `COUNT(*) FROM loans_fact` | PASS (1,432,440) |
| 8 | `execute_query_tool` | JOIN + GROUP BY top loan status | PASS (Current 702,223 / Fully Paid 551,955 …) |
| 9 | `preview_table` | `loan_status_dim` limit 5 | PASS |

### Resources (2)
| # | Resource | Result |
|---|----------|--------|
| 10 | `resources/list` | PASS (mssql://tables, mssql://schema/{table_name}) |
| 11 | `resources/read` → `mssql://tables` | PASS (6 tables) |
| 12 | `resources/read` → `mssql://schema/loans_fact` | PASS (full column schema) |

### Prompts (2)
| # | Prompt | Result |
|---|--------|--------|
| 17 | `data_analysis_template("loans_fact")` | PASS (template generated with all 14 real columns) |
| 18 | `generate_sql_query("count loans by status")` | PASS (prompt includes live schema of all dim tables) |

> Prompts are defined via FastMCP decorators in `app/mcp_server.py`. The HTTP dispatcher in
> `main.py` routes `tools/*` and `resources/*`; the prompt functions were exercised directly
> against the live DB to confirm they generate correct output with real schema.

## How to reproduce
```bash
# server running on :8044 with DB env vars (DB_SERVER/DB_NAME/DB_USER/DB_PASSWORD)
python3 test_all_tools.py        # see ../../test_all_tools.py in repo root of this PR
```
