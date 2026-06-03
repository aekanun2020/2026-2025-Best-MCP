# MSSQL MCP Server with Streamable HTTP Transport

A Model Context Protocol (MCP) server that provides SQL Server database access through Streamable HTTP transport, containerized with Docker.

## Features

- **Streamable HTTP Transport**: Single-endpoint HTTP transport (the current MCP standard, replacing HTTP+SSE)
- **MSSQL Integration**: Connect to Microsoft SQL Server databases
- **FastAPI Backend**: Modern, fast web framework
- **Docker Support**: Fully containerized application
- **MCP Tools**: 
  - Execute SQL queries
  - Preview tables
  - Get database information
  - Refresh schema cache
- **MCP Resources**:
  - List all tables
  - Get table schemas
- **MCP Prompts**:
  - Data analysis templates
  - SQL query generation

## Installation

> **Prerequisites:** Install and start **Docker Desktop** first ([Mac](https://docs.docker.com/desktop/install/mac-install/) / [Windows](https://docs.docker.com/desktop/install/windows-install/)). Make sure your SQL Server is running on the host machine and listening on port **1433**, and that local port **9000** is free.

The steps differ slightly between Windows and Mac. Follow the section for your OS.

---

### Windows (double-click)

**1. Download the project from GitHub**

Open `Command Prompt` (CMD) and run:

```cmd
git clone https://github.com/aekanun2020/2026-2025-Best-MCP.git
cd 2026-2025-Best-MCP\mssql-mcp-server-streamablehttp
```

(No Git? Click the green **Code ▾** button on the [repo page](https://github.com/aekanun2020/2026-2025-Best-MCP) → **Download ZIP** → unzip → open the `mssql-mcp-server-streamablehttp` folder.)

**2. Start the server**

Open the `mssql-mcp-server-streamablehttp` folder in File Explorer and **double-click `start_docker.bat`**.

A CMD window opens and does everything for you:
- creates `.env` from `.env.example` (if it doesn't exist yet)
- builds the Docker image
- starts the container and streams its logs

**3. Done**

The server is running at **http://localhost:9000/mcp** once you see the health logs.
Keep the CMD window open — **closing it stops the server.** To stop, close the window or press `Ctrl + C`.

---

### Mac (Terminal)

**1. Download the project from GitHub**

Open `Terminal` and run:

```bash
git clone https://github.com/aekanun2020/2026-2025-Best-MCP.git
cd 2026-2025-Best-MCP/mssql-mcp-server-streamablehttp
```

**2. Start the server**

```bash
chmod +x start_docker.sh   # only needed the first time
./start_docker.sh
```

The script creates `.env` from `.env.example` (if missing), builds the image, starts the container, and streams its logs.

**3. Done**

The server is running at **http://localhost:9000/mcp** once you see the health logs.
Keep the Terminal open — closing it (or pressing `Ctrl + C`) stops the server.

---

### Database configuration

The installer copies [`.env.example`](.env.example) to `.env` for you, pre-set for a SQL Server running on the **same machine** as Docker Desktop:

```env
DB_SERVER=host.docker.internal
DB_NAME=TestDB
DB_USER=SA
DB_PASSWORD=Passw0rd123456
```

`host.docker.internal` lets the container reach SQL Server on your host machine. If your database lives elsewhere, edit `.env` (then re-run the start script) and change `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` accordingly.

## Managing the container

The container name is **`mssql-mcp-streamable-http`**. Run these from the `mssql-mcp-server-streamablehttp` folder.

```bash
# Check status / health
docker ps

# View live logs
docker logs -f mssql-mcp-streamable-http

# Stop the server (keeps the container so you can start it again)
docker compose stop

# Start it again later
docker compose start
```

## Re-running with a new configuration

If you change `.env` (for example a different `DB_SERVER` or password), apply the new
configuration by **rebuilding and recreating** the container in place:

```bash
docker compose up -d --build --force-recreate
```

> **Do NOT run `docker compose down`.** `down` removes the container together with its
> network (and can drop other associated resources), which is unnecessary and can
> interrupt anything else relying on it. `up -d --build --force-recreate` already
> recreates the container in place with your new `.env`/config — this is the only command
> you need to re-apply changes.

## API Endpoints

- `POST /mcp` - MCP message endpoint (Streamable HTTP, **stateless**)
- `GET /mcp` - SSE stream endpoint (returns 405 if the server does not offer a stream)
- `DELETE /mcp` - Terminate an MCP session (no-op when stateless; always returns 200)
- `GET /health` - Health check endpoint
- `GET /` - API documentation

### Session handling (stateless)

This server runs in **stateless** mode (similar to FastMCP's `stateless_http=True`).
An `Mcp-Session-Id` is minted and returned on `initialize` for compatibility,
but subsequent requests are accepted **with or without** the `Mcp-Session-Id` header.
This lets clients that do not echo back the session id (e.g. PyClaw's Streamable HTTP path) work without modification.

**Note:** When using Docker, the server runs internally on port 8000 but is exposed externally on port 9000.

## MCP Client Configuration

For Claude Desktop or other MCP clients, connect through `mcp-remote` (it bridges a
Streamable HTTP server into the stdio interface these clients expect):

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

Replace `localhost` with the server's IP (e.g. a LAN or Tailscale address) if the client
runs on a different machine than the server. `--allow-http` is required because the
server is served over plain HTTP, not HTTPS.

## License

MIT
