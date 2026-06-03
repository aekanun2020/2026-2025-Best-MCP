#!/usr/bin/env python3
"""End-to-end test for RAG MCP Streamable HTTP server (stateless).

Tests protocol handshake + all 4 tools against a running container.
Usage: python test_all_tools.py [base_url]   (default http://localhost:9000/mcp)
"""
import sys
import json
import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9000/mcp"
ROOT = BASE.rsplit("/mcp", 1)[0]

HDR = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def rpc(method, params=None, _id=1, session=None):
    body = {"jsonrpc": "2.0", "id": _id, "method": method, "params": params or {}}
    h = dict(HDR)
    if session:
        h["MCP-Session-Id"] = session
    r = httpx.post(BASE, json=body, headers=h, timeout=120)
    return r


def line(label, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}" + (f"  -- {detail}" if detail else ""))
    return ok


def main():
    results = []

    # 1. health
    r = httpx.get(f"{ROOT}/health", timeout=30)
    results.append(line("GET /health", r.status_code == 200, r.text.strip()))

    # 2. initialize -> mints session id (optional), returns JSON directly
    r = rpc("initialize", {"protocolVersion": "2025-11-25",
                           "capabilities": {"tools": {}},
                           "clientInfo": {"name": "test", "version": "0.1"}})
    sid = r.headers.get("MCP-Session-Id")
    j = r.json()
    proto = j.get("result", {}).get("protocolVersion")
    results.append(line("POST initialize (JSON body + session header)",
                        r.status_code == 200 and proto == "2025-11-25" and bool(sid),
                        f"proto={proto} session={sid[:8] if sid else None}..."))

    # 3. GET /mcp without event-stream Accept -> 405
    r = httpx.get(BASE, headers={"Accept": "application/json"}, timeout=30)
    results.append(line("GET /mcp without text/event-stream", r.status_code == 405,
                        f"HTTP {r.status_code}"))

    # 4. tools/list -- STATELESS: send NO session id, expect 4 tools
    r = rpc("tools/list", _id=2)
    tools = [t["name"] for t in r.json().get("result", {}).get("tools", [])]
    expected = {"search_documentation", "list_sources", "add_directory", "add_context"}
    results.append(line("tools/list (no session id -> stateless)",
                        r.status_code == 200 and set(tools) == expected,
                        f"tools={tools}"))

    # 5. tool: add_context (write a doc into RAG)
    r = rpc("tools/call", {"name": "add_context", "arguments": {
        "content": "PyRAGDoc รองรับ Hybrid Search รวม BM25 และ Semantic ด้วย RRF. "
                   "ระบบนี้รองรับภาษาไทยและเลขไทย ๑๒๓.",
        "title": "RAG Test Note",
        "source": "e2e_test"}}, _id=3)
    txt = json.dumps(r.json().get("result", {}), ensure_ascii=False)
    results.append(line("tools/call add_context", r.status_code == 200 and "error" not in r.json(),
                        txt[:160]))

    # 6. tool: list_sources -- should now include e2e_test
    r = rpc("tools/call", {"name": "list_sources", "arguments": {}}, _id=4)
    txt = json.dumps(r.json().get("result", {}), ensure_ascii=False)
    results.append(line("tools/call list_sources", r.status_code == 200 and "error" not in r.json(),
                        txt[:160]))

    # 7. tool: search_documentation (hybrid) -- should retrieve the added note
    r = rpc("tools/call", {"name": "search_documentation",
                          "arguments": {"query": "Hybrid Search ภาษาไทย", "limit": 3}}, _id=5)
    txt = json.dumps(r.json().get("result", {}), ensure_ascii=False)
    results.append(line("tools/call search_documentation", r.status_code == 200 and "error" not in r.json(),
                        txt[:200]))

    # 8. tool: add_directory (the container has /home/mcpuser/documents seeded? not in this dir)
    #    point at the app dir which exists; expect a non-error structured reply.
    r = rpc("tools/call", {"name": "add_directory", "arguments": {"path": "/home/mcpuser/documents"}}, _id=6)
    txt = json.dumps(r.json().get("result", {}), ensure_ascii=False)
    results.append(line("tools/call add_directory", r.status_code == 200 and "error" not in r.json(),
                        txt[:160]))

    # 9. DELETE /mcp -- terminate the session we minted (expect 204)
    r = httpx.request("DELETE", BASE, headers={"MCP-Session-Id": sid} if sid else {}, timeout=30)
    results.append(line("DELETE /mcp (terminate session)", r.status_code in (204, 200),
                        f"HTTP {r.status_code}"))

    print("\n" + "=" * 60)
    passed = sum(1 for x in results if x)
    print(f"RESULT: {passed}/{len(results)} checks passed")
    print("=" * 60)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
