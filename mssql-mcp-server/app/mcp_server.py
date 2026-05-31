"""
MCP Server implementation with SSE transport
"""
import json
import logging
from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

from .database import (
    db_cache, execute_query, get_database_info, get_table_schema,
    DB_NAME, DB_SERVER
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp_server = FastMCP("mssql-sse-server")

# Initialize SSE transport
sse_transport = SseServerTransport("/messages")

# Initialize database cache on startup
db_cache.refresh()

# MCP Resources
@mcp_server.resource(uri="mssql://tables")
async def list_tables() -> str:
    """List all tables in the database"""
    tables = db_cache.get_tables()
    return json.dumps(tables, indent=2)

@mcp_server.resource(uri="mssql://schema/{table_name}")
async def get_schema(table_name: str) -> str:
    """Get the schema for a specific table
    
    Args:
        table_name: Name of the table
    """
    schema = db_cache.get_schema(table_name)
    
    if not schema:
        return json.dumps({"error": f"Table {table_name} not found or error fetching schema"})
    
    return json.dumps(schema, indent=2)

# MCP Tools
@mcp_server.tool()
async def execute_query_tool(query: str) -> str:
    """Run an arbitrary T-SQL query and return the result rows as text.

    WHEN TO USE:
        - Any question that needs filtering, aggregation, sorting, joins, or
          exact answers: COUNT / SUM / AVG / WHERE / GROUP BY / ORDER BY / JOIN.
        - "How many...", "total...", "top N by...", "for year 2025 only...".
        - Call get_database_context() FIRST so you know table/column names and
          relationships, then write a correct query here.

    WHEN NOT TO USE:
        - Just to eyeball what a table looks like -> use preview_table instead.
        - To discover schema/relationships -> use get_database_context instead.
        - Do NOT answer counting/total/ranking questions from preview_table rows;
          always compute them with a real query here.

    ARGS:
        query (str): A single T-SQL statement. Must be non-empty.
            Use T-SQL syntax: SELECT TOP n (not LIMIT), GETDATE() (not NOW()).
            This server runs against Microsoft SQL Server.

    SECURITY:
        The read-only (SELECT-only) guard is currently disabled, so this tool
        CAN run INSERT/UPDATE/DELETE/DROP. For a read-only deployment, enable the
        guard below. A non-SELECT statement raises ValueError when the guard is on.

    RETURNS (JSON string):
        Success: {"result": "<rows as text>"}. Results larger than 10,000 chars
            are truncated to the first 100 rows with a note.
        Empty:   {"result": "Query executed successfully but returned no results."}
        DB error / bad SQL / no connection: {"error": "<message>"} (does NOT raise;
            inspect the 'error' field before using the output).

    RAISES:
        ValueError: if query is empty/whitespace (or non-SELECT when the guard is enabled).
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("`query` must be a non-empty SQL string.")
    query = query.strip()

    # Read-only guard. Enable for production to reject write statements.
    # if not query.lower().startswith('select'):
    #     raise ValueError("Only SELECT queries are allowed (read-only mode).")

    result = execute_query(query)
    return json.dumps(result)

@mcp_server.tool()
async def preview_table(table_name: str, limit: int = 10) -> str:
    """Peek at a few sample rows from a table (SELECT TOP n * FROM table).

    WHEN TO USE:
        - To see what a table's data looks like before writing a real query.
        - To inspect column values, formats, and example content.

    WHEN NOT TO USE (IMPORTANT):
        - Do NOT use the returned rows to answer counting, total, average, max/min,
          filtered, or ranking questions. There is NO WHERE and NO ORDER BY, so the
          rows are an arbitrary slice, NOT the "first N" or "top N" in any logical
          sense and the order is not guaranteed. For those questions use
          execute_query_tool with proper WHERE / ORDER BY / aggregate functions.
        - Do NOT summarize a large table from this small sample.

    ARGS:
        table_name (str): Exact table name as returned by get_database_context /
            list_tables. Must be non-empty. Wrapped in [brackets] automatically.
        limit (int): Number of sample rows. Accepted range 1-1000.
            Default 10. Values > 1000 are capped to 1000; values < 1 raise ValueError.

    RETURNS (JSON string):
        Success: {"result": "<sample rows as text>"}
        Empty table: {"result": "Query executed successfully but returned no results."}
        Unknown table / DB error: {"error": "<message>"} (does NOT raise;
            check the 'error' field, e.g. an invalid table name surfaces here).

    RAISES:
        ValueError: if table_name is empty, or limit is not a positive integer.
    """
    if not isinstance(table_name, str) or not table_name.strip():
        raise ValueError("`table_name` must be a non-empty string.")
    table_name = table_name.strip()

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        raise ValueError("`limit` must be an integer between 1 and 1000.")
    if limit < 1:
        raise ValueError("`limit` must be >= 1.")
    if limit > 1000:
        limit = 1000  # Cap the maximum for safety

    query = f"SELECT TOP {limit} * FROM [{table_name}]"
    result = execute_query(query)
    return json.dumps(result)

@mcp_server.tool()
async def get_database_info_tool() -> str:
    """Get high-level metadata about the database (not the data itself).

    WHEN TO USE:
        - When you need the database name, server, table count, SQL Server
          version, or database size in MB.

    WHEN NOT TO USE:
        - To read table contents -> use preview_table or execute_query_tool.
        - To get column-level schema / relationships -> use get_database_context.

    ARGS:
        none.

    RETURNS (JSON string):
        {"database_name", "server", "table_count", "server_version", "size_mb"}.
        On failure: {"error": "..."}, or the same object with an extra "error"
        key if only part of the lookup failed (does NOT raise).
    """
    info = get_database_info()
    return json.dumps(info, indent=2)

@mcp_server.tool()
async def refresh_db_cache() -> str:
    """Reload the cached table list, schemas, and relationship graph from the DB.

    WHEN TO USE:
        - After the database structure changes (tables/columns/foreign keys added,
          dropped, or renamed) so get_database_context returns fresh information.

    WHEN NOT TO USE:
        - As part of answering normal data questions; the cache is already loaded
          at startup. Refreshing re-queries metadata for every table and is slower.

    ARGS:
        none.

    RETURNS (JSON string):
        {"status": "success", "message": "Cache refreshed. Found N tables."}.
        If the DB is unreachable the table count is 0 (the underlying calls return
        empty rather than raising).
    """
    db_cache.refresh()
    return json.dumps({
        "status": "success",
        "message": f"Cache refreshed. Found {len(db_cache.get_tables())} tables."
    })


@mcp_server.tool()
async def get_database_context() -> str:
    """Get the full database structure: schemas, relationships, and a T-SQL guide.

    WHEN TO USE:
        - ALWAYS call this FIRST, before writing any query, so you use correct
          table names, column names, data types, and join paths.
        - When you need to know which tables relate via foreign keys and which can
          be queried standalone (loner tables).

    WHEN NOT TO USE:
        - To read actual row data -> use preview_table or execute_query_tool.
        - Repeatedly in a loop; the result is cached, but it is large. Call once
          per session unless the schema changed (then call refresh_db_cache first).

    ARGS:
        none.

    RETURNS (JSON string), an object with:
        - database_info: {name, server, table_count, tables[]}
        - tsql_syntax_guide: T-SQL reminders (TOP not LIMIT, GETDATE not NOW, etc.)
        - relationships: {has_relationships, relationship_count, foreign_keys[],
          loner_tables[], query_hints}
        - table_schemas: per-table column list (name, type, max_length, nullable, default)
        - common_queries: ready-made INFORMATION_SCHEMA snippets
        Served from cache (~ms when warm). Does NOT raise; if the DB was unreachable
        at cache load, lists may be empty.
    """
    
    tables = db_cache.get_tables()
    table_count = len(tables)
    relationship_graph = db_cache.get_relationship_graph()
    
    # Build comprehensive context
    context = {
        "database_info": {
            "name": DB_NAME,
            "server": DB_SERVER,
            "table_count": table_count,
            "tables": tables
        },
        
        "tsql_syntax_guide": {
            "limit_rows": "SELECT TOP 10 * FROM table (NOT LIMIT 10)",
            "current_date": "GETDATE() (NOT NOW())",
            "string_concat": "+ or CONCAT()",
            "date_format": "CONVERT(VARCHAR, date, 120)"
        },
        
        "relationships": relationship_graph,
        
        "table_schemas": {},
        
        "common_queries": {
            "list_tables": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'",
            "get_schema": "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='YourTable'"
        }
    }
    
    # Add FK-specific syntax only if relationships exist
    if relationship_graph["has_relationships"]:
        context["tsql_syntax_guide"]["foreign_keys"] = "SELECT * FROM sys.foreign_keys (NOT INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS)"
        context["tsql_syntax_guide"]["joins"] = "Use proper JOIN syntax with ON clause"
        context["common_queries"]["view_fks"] = "SELECT f.name, OBJECT_NAME(f.parent_object_id) AS ParentTable FROM sys.foreign_keys f"
    
    # Get schema for each table
    for table in tables:
        schema = db_cache.get_schema(table)
        if schema:
            context["table_schemas"][table] = schema
    
    return json.dumps(context, indent=2)

# MCP Prompts
@mcp_server.prompt()
async def data_analysis_template(table_name: str) -> Dict:
    """Generate a template for analyzing a specific table
    
    Args:
        table_name: Name of the table to analyze
    """
    schema = db_cache.get_schema(table_name)
    
    if not schema:
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"The table {table_name} was not found in the database. Please check the table name and try again."
                    }
                }
            ]
        }
    
    column_names = [col["name"] for col in schema]
    
    analysis_template = f"""
I need to analyze the data in the {table_name} table. The table has the following columns:
{', '.join(column_names)}

Please help me:
1. Understand the basic statistics and distribution of values in each column
2. Identify any trends or patterns in the data
3. Find correlations between different columns
4. Create visualizations to represent the data effectively
5. Provide insights and recommendations based on the data

Here's a sample SQL query to start exploring the table:
```sql
SELECT TOP 10 * FROM [{table_name}]
```

What other analyses would you recommend for this table?
"""
    
    return {
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": analysis_template
                }
            }
        ]
    }

@mcp_server.prompt()
async def generate_sql_query(description: str) -> Dict:
    """Generate a SQL query based on a natural language description
    
    Args:
        description: Natural language description of the query to generate
    """
    tables = db_cache.get_tables()
    table_info = {}
    
    # Get schema for up to 5 tables
    for table in tables[:5]:
        schema = db_cache.get_schema(table)
        if schema:
            table_info[table] = [col["name"] for col in schema]
    
    tables_schemas = ""
    for table, columns in table_info.items():
        tables_schemas += f"\nTable: {table}\nColumns: {', '.join(columns)}\n"
    
    query_prompt = f"""
I need help generating a SQL query for a Microsoft SQL Server database (T-SQL syntax).

The database contains the following tables and columns:
{tables_schemas}

Please write a SQL query that does the following:
{description}

Remember:
- Use proper T-SQL syntax
- Only use SELECT statements (read-only)
- Include comments to explain your query
- If you need to join tables, explain the relationships
"""
    
    return {
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": query_prompt
                }
            }
        ]
    }
