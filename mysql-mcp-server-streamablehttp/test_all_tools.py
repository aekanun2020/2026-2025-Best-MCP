#!/usr/bin/env python3
"""
End-to-end test of ALL tools/resources/prompts on the
Streamable HTTP MCP server (mysql-mcp-server-streamablehttp),
talking to a LIVE MySQL server.

Runs real HTTP requests against POST /mcp following the MCP
Streamable HTTP spec. This server runs in STATELESS mode, so the
session-id lifecycle is optional: every request is accepted with or
without an Mcp-Session-Id header.

Set BASE via the MCP_BASE_URL env var (default http://127.0.0.1:8000).
"""
import json
import os
import sys
import urllib.request
import urllib.error

BASE = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8000")
MCP = BASE + "/mcp"

results = []   # collected for the report / screenshots


def post(payload, session_id=None):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(MCP, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Origin", BASE)
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


# Discover a real table name to exercise preview/schema against.
def discover_table(session_id=None):
    st, body, _ = post(jrpc("tools/call", {
        "name": "execute_query_tool",
        "arguments": {"query": (
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' LIMIT 1"
        )}
    }, _id=99), session_id=session_id)
    try:
        text = json.loads(body)["result"]["content"][0]["text"]
        # text is the pandas to_string output; last token of last line is the value
        lines = [l for l in text.splitlines() if l.strip()]
        return lines[-1].strip().split()[-1]
    except Exception:
        return None


print("=" * 70)
print("MCP Streamable HTTP server (MySQL) -- FULL TOOL TEST against live DB")
print("=" * 70)

# 1) initialize -> returns a session id (optional in stateless mode)
st, body, sid = post(jrpc("initialize", {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "e2e-tester", "version": "1.0"},
}))
record("1. initialize", st, body, ok=(st == 200 and sid is not None),
       note=f"Mcp-Session-Id={sid}")
SESSION = sid

# 2) notifications/initialized -> 202, no body
st, body, _ = post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id=SESSION)
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

# 5) tool: refresh_db_cache (no args)
st, body, _ = post(jrpc("tools/call", {"name": "refresh_db_cache", "arguments": {}}, _id=4), session_id=SESSION)
record("5. tool: refresh_db_cache", st, body, ok=(st == 200 and "success" in body))

# 6) tool: get_database_context (no args)
st, body, _ = post(jrpc("tools/call", {"name": "get_database_context", "arguments": {}}, _id=5), session_id=SESSION)
record("6. tool: get_database_context", st, body, ok=(st == 200 and "mysql_syntax_guide" in body))

# 7) tool: execute_query_tool -- simple scalar
st, body, _ = post(jrpc("tools/call", {
    "name": "execute_query_tool",
    "arguments": {"query": "SELECT COUNT(*) AS table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=DATABASE()"}
}, _id=6), session_id=SESSION)
record("7. tool: execute_query_tool (COUNT)", st, body, ok=(st == 200 and "table_count" in body))

# discover a real table for the next checks
TABLE = discover_table(SESSION)
print(f"[info] discovered table for preview/schema tests: {TABLE}")

# 8) tool: execute_query_tool -- aggregate via INFORMATION_SCHEMA (always available)
st, body, _ = post(jrpc("tools/call", {
    "name": "execute_query_tool",
    "arguments": {"query": (
        "SELECT TABLE_NAME, TABLE_ROWS FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME LIMIT 5"
    )}
}, _id=7), session_id=SESSION)
record("8. tool: execute_query_tool (ORDER BY + LIMIT)", st, body, ok=(st == 200 and '"error"' not in body))

# 9) tool: preview_table
if TABLE:
    st, body, _ = post(jrpc("tools/call", {
        "name": "preview_table",
        "arguments": {"table_name": TABLE, "limit": 5}
    }, _id=8), session_id=SESSION)
    record(f"9. tool: preview_table ({TABLE}, limit 5)", st, body, ok=(st == 200 and '"error"' not in body))
else:
    record("9. tool: preview_table", 0, "no table discovered", ok=False)

# 10) resources/list
st, body, _ = post(jrpc("resources/list", _id=9), session_id=SESSION)
record("10. resources/list", st, body, ok=(st == 200 and "mysql://tables" in body))

# 11) resources/read -> mysql://tables
st, body, _ = post(jrpc("resources/read", {"uri": "mysql://tables"}, _id=10), session_id=SESSION)
record("11. resources/read (mysql://tables)", st, body, ok=(st == 200 and '"error"' not in body))

# 12) resources/read -> mysql://schema/<table>
if TABLE:
    st, body, _ = post(jrpc("resources/read", {"uri": f"mysql://schema/{TABLE}"}, _id=11), session_id=SESSION)
    record(f"12. resources/read (mysql://schema/{TABLE})", st, body, ok=(st == 200 and '"error"' not in body))
else:
    record("12. resources/read (schema)", 0, "no table discovered", ok=False)

# 13) protocol: GET /mcp -> 405 (no standalone SSE stream)
req = urllib.request.Request(MCP, method="GET")
try:
    r = urllib.request.urlopen(req, timeout=15); gst = r.status; gbody = r.read().decode()
except urllib.error.HTTPError as e:
    gst = e.code; gbody = e.read().decode()
record("13. protocol: GET /mcp (no stream)", gst, gbody or "(empty 405)", ok=(gst == 405))

# 14) protocol: tools/list with NO session -> 200 (STATELESS: accepted)
st, body, _ = post(jrpc("tools/list", _id=12))
record("14. protocol: tools/list (no session, stateless)", st, body, ok=(st == 200))

# 15) protocol: tools/list with arbitrary session id -> 200 (STATELESS: ignored)
st, body, _ = post(jrpc("tools/list", _id=13), session_id="00000000-0000-0000-0000-000000000000")
record("15. protocol: tools/list (arbitrary session, stateless)", st, body, ok=(st == 200))

# 16) protocol: DELETE /mcp -> 200 (terminate is a no-op in stateless)
req = urllib.request.Request(MCP, method="DELETE")
if SESSION:
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
