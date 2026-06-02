#!/usr/bin/env python3
"""
Debug test for Streamable HTTP endpoint
"""
import httpx
import asyncio
import json

MCP_URL = "http://localhost:9000/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": "2024-11-05",
}


async def test_streamable_http_proper():
    """Test Streamable HTTP with proper session handling"""
    print("Testing Streamable HTTP MCP Server...")

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        print("\n1. Sending initialize...")

        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        resp = await client.post(MCP_URL, json=init_message, headers=HEADERS)
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   Error: {resp.text}")
            return

        data = resp.json()
        print(f"   Initialize response: {json.dumps(data, indent=2)}")

        # Capture the session id assigned by the server
        session_id = resp.headers.get("mcp-session-id")
        print(f"   Got session id: {session_id}")

        # All subsequent requests must echo the session id
        session_headers = dict(HEADERS)
        if session_id:
            session_headers["Mcp-Session-Id"] = session_id

        print("\n2. Sending initialized notification...")
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        resp = await client.post(MCP_URL, json=initialized, headers=session_headers)
        print(f"   Status: {resp.status_code}")

        # Test tools/list
        print("\n3. Testing tools/list...")
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        resp = await client.post(MCP_URL, json=tools_msg, headers=session_headers)
        print(f"   Status: {resp.status_code}")

        print("\n4. Reading tools response...")
        if resp.status_code == 200:
            data = resp.json()
            print("\n   Tools available:")
            for tool in data.get("result", {}).get("tools", []):
                print(f"   - {tool.get('name')}: {tool.get('description')}")


if __name__ == "__main__":
    asyncio.run(test_streamable_http_proper())
