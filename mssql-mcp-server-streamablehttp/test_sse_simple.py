#!/usr/bin/env python3
"""
Test script for Streamable HTTP MCP Server - Simple version
"""
import asyncio
import json
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server URL
SERVER_URL = "http://localhost:9000/mcp"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": "2024-11-05",
}


async def test_streamable_http_connection():
    """Test basic Streamable HTTP connection"""
    logger.info(f"Testing Streamable HTTP connection to {SERVER_URL}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health check first
        logger.info("Testing health check...")
        health_response = await client.get("http://localhost:9000/health")
        logger.info(f"Health check response: {health_response.json()}")

        # Send initialize message to the MCP endpoint
        logger.info("Sending initialize to MCP endpoint...")
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

        init_response = await client.post(SERVER_URL, json=init_message, headers=HEADERS)
        logger.info(f"Initialize response status: {init_response.status_code}")
        logger.info(f"Initialize response: {init_response.text}")

        # Capture the session id assigned by the server
        session_id = init_response.headers.get("mcp-session-id")
        logger.info(f"Session ID: {session_id}")

        session_headers = dict(HEADERS)
        if session_id:
            session_headers["Mcp-Session-Id"] = session_id

        # Test tools/list
        logger.info("Testing tools/list...")
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        tools_response = await client.post(SERVER_URL, json=tools_message, headers=session_headers)
        logger.info(f"Tools/list response status: {tools_response.status_code}")
        if tools_response.status_code == 200:
            tools_data = tools_response.json()
            logger.info(f"Got tools list: {tools_data}")


async def main():
    """Main test function"""
    try:
        await test_streamable_http_connection()
        logger.info("Test completed!")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
