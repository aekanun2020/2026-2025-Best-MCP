#!/usr/bin/env python3
"""
End-to-end test of ALL tools/resources/prompts on the new
Streamable HTTP MCP server (mssql-mcp-server-streamablehttp),
talking to the LIVE SQL Server (TestDB) through the cloudflared tunnel.

Runs real HTTP requests against POST /mcp following the MCP
Streamable HTTP spec (Mcp-Session-Id header lifecycle).
"""
import json
import sys
import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8044"
MCP = BASE + "/mcp"

results = []   # collected for the report / screenshots


def post(payload, session_id=None, expect_status=200):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(MCP, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("Origin", "http://127.0.0.1:8044")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        status = resp.status
        body = resp.read().decode()
        sid = resp.headers.get("Mcp-Session-Id")
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode()
        sid = e.headers.get("Mcp-Session-Id")
    return status, body, sid


def jrpc(method, params=None, _id=1):
    p = {"jsonrpc": "2.0", "id": _id, "method": method}
    if params is not None:
        p["params"] = params
    return p


def record(label, status, body, ok, note=""):
    try:
        parsed = json.loads(body)
        pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        pretty = body
    # truncate very long bodies for the screenshot
    if len(pretty) > 1400:
        pretty = pretty[:1400] + "\n... (truncated)"
    results.append({
        "label": label, "status": status, "ok": ok,
        "note": note, "body": pretty,
    })
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}  (HTTP {status}) {note}")
    print(pretty)
    print("-" * 70)


print("=" * 70)
print("MCP Streamable HTTP server -- FULL TOOL TEST against live TestDB")
print("=" * 70)

# 1) initialize -> must return a session id
st, body, sid = post(jrpc("initialize", {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {"name": "e2e-tester", "version": "1.0"},
}))
record("1. initialize", st, body, ok=(st == 200 and sid is not None),
       note=f"Mcp-Session-Id={sid}")
SESSION = sid

# 2) notifications/initialized -> 202, no body
st, body, _ = post(jrpc_n := {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id=SESSION)
record("2. notifications/initialized", st, body or "(empty 202)", ok=(st == 202))

# 3) tools/list -> 5 tools
st, body, _ = post(jrpc("tools/list", _id=2), session_id=SESSION)
try:
    n_tools = len(json.loads(body)["result"]["tools"])
except Exception:
    n_tools = -1
record("3. tools/list", st, body, ok=(st == 200 and n_tools == 5),
       note=f"{n_tools} tools")

# 4) tool: get_database_info_tool (no args)
st, body, _ = post(jrpc("tools/call", {"name": "get_database_info_tool", "arguments": {}}, _id=3), session_id=SESSION)
record("4. tool: get_database_info_tool", st, body, ok=(st == 200 and '"error"' not in body))

# 5) tool: refresh_db_cache (no args) -- can be slow over tunnel
st, body, _ = post(jrpc("tools/call", {"name": "refresh_db_cache", "arguments": {}}, _id=4), session_id=SESSION)
record("5. tool: refresh_db_cache", st, body, ok=(st == 200 and '"error"' not in body))

# 6) tool: get_database_context (no args)
st, body, _ = post(jrpc("tools/call", {"name": "get_database_context", "arguments": {}}, _id=5), session_id=SESSION)
record("6. tool: get_database_context", st, body, ok=(st == 200 and '"error"' not in body))

# 7) tool: execute_query_tool -- COUNT on fact table
st, body, _ = post(jrpc("tools/call", {
    "name": "execute_query_tool",
    "arguments": {"query": "SELECT COUNT(*) AS total_rows FROM loans_fact"}
}, _id=6), session_id=SESSION)
record("7. tool: execute_query_tool (COUNT)", st, body, ok=(st == 200 and "total_rows" in body))

# 8) tool: execute_query_tool -- JOIN + GROUP BY
st, body, _ = post(jrpc("tools/call", {
    "name": "execute_query_tool",
    "arguments": {"query": (
        "SELECT TOP 5 ls.loan_status, COUNT(*) AS cnt "
        "FROM loans_fact f JOIN loan_status_dim ls "
        "ON f.loan_status_id = ls.loan_status_id "
        "GROUP BY ls.loan_status ORDER BY cnt DESC"
    )}
}, _id=7), session_id=SESSION)
record("8. tool: execute_query_tool (JOIN+GROUP BY)", st, body, ok=(st == 200 and '"error"' not in body))

# 9) tool: preview_table
st, body, _ = post(jrpc("tools/call", {
    "name": "preview_table",
    "arguments": {"table_name": "loan_status_dim", "limit": 5}
}, _id=8), session_id=SESSION)
record("9. tool: preview_table (loan_status_dim, limit 5)", st, body, ok=(st == 200 and '"error"' not in body))

# 10) resources/list
st, body, _ = post(jrpc("resources/list", _id=9), session_id=SESSION)
record("10. resources/list", st, body, ok=(st == 200 and "mssql://tables" in body))

# 11) resources/read -> mssql://tables
st, body, _ = post(jrpc("resources/read", {"uri": "mssql://tables"}, _id=10), session_id=SESSION)
record("11. resources/read (mssql://tables)", st, body, ok=(st == 200 and '"error"' not in body))

# 12) resources/read -> mssql://schema/loans_fact
st, body, _ = post(jrpc("resources/read", {"uri": "mssql://schema/loans_fact"}, _id=11), session_id=SESSION)
record("12. resources/read (mssql://schema/loans_fact)", st, body, ok=(st == 200 and '"error"' not in body))

# 13) protocol: GET /mcp -> 405
req = urllib.request.Request(MCP, method="GET")
req.add_header("Mcp-Session-Id", SESSION)
try:
    r = urllib.request.urlopen(req, timeout=15); gst = r.status; gbody = r.read().decode()
except urllib.error.HTTPError as e:
    gst = e.code; gbody = e.read().decode()
record("13. protocol: GET /mcp (no stream)", gst, gbody, ok=(gst == 405))

# 14) protocol: tools/list with NO session -> 400
st, body, _ = post(jrpc("tools/list", _id=12))
record("14. protocol: tools/list (no session)", st, body, ok=(st == 400))

# 15) protocol: bad session -> 404
st, body, _ = post(jrpc("tools/list", _id=13), session_id="00000000-bad-bad-bad-000000000000")
record("15. protocol: tools/list (bad session)", st, body, ok=(st == 404))

# 16) protocol: DELETE /mcp -> 200 (terminate session)
req = urllib.request.Request(MCP, method="DELETE")
req.add_header("Mcp-Session-Id", SESSION)
try:
    r = urllib.request.urlopen(req, timeout=15); dst = r.status; dbody = r.read().decode()
except urllib.error.HTTPError as e:
    dst = e.code; dbody = e.read().decode()
record("16. protocol: DELETE /mcp (terminate)", dst, dbody or "(empty 200)", ok=(dst == 200))

# summary
passed = sum(1 for r in results if r["ok"])
total = len(results)
print("=" * 70)
print(f"SUMMARY: {passed}/{total} checks passed")
print("=" * 70)

with open("/home/user/workspace/test_results.json", "w", encoding="utf-8") as f:
    json.dump({"passed": passed, "total": total, "results": results}, f, ensure_ascii=False, indent=2)

sys.exit(0 if passed == total else 1)
