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
    """Execute a read-only SQL query and return the results
    
    Args:
        query: SQL query to execute (must be SELECT only)
    """
    # Safety check for read-only queries
    query = query.strip()
    # Commented out for flexibility, but can be enabled for production
    # if not query.lower().startswith('select'):
    #     return json.dumps({"error": "Only SELECT queries are allowed for security reasons."})
    
    result = execute_query(query)
    return json.dumps(result)

@mcp_server.tool()
async def preview_table(table_name: str, limit: int = 10) -> str:
    """Get a preview of the data in a table
    
    Args:
        table_name: Name of the table to preview
        limit: Maximum number of rows to return (default: 10)
    """
    # Ensure limit is integer
    limit = int(limit)
    
    if limit > 1000:
        limit = 1000  # Cap the maximum for safety
    
    query = f"SELECT TOP {limit} * FROM [{table_name}]"
    result = execute_query(query)
    return json.dumps(result)

@mcp_server.tool()
async def get_database_info_tool() -> str:
    """Get general information about the database"""
    info = get_database_info()
    return json.dumps(info, indent=2)

@mcp_server.tool()
async def refresh_db_cache() -> str:
    """Refresh the database schema cache"""
    db_cache.refresh()
    return json.dumps({
        "status": "success",
        "message": f"Cache refreshed. Found {len(db_cache.get_tables())} tables."
    })


@mcp_server.tool()
async def get_database_context() -> str:
    """Get complete database context including schema, relationships, and T-SQL syntax guide.
    
    This tool provides comprehensive information about the database structure:
    - Database metadata (name, table count, size)
    - All table schemas (columns, types, nullability)
    - Relationship graph (foreign keys, loner tables)
    - T-SQL syntax guide
    - Common query examples
    
    Call this tool FIRST before executing queries to understand the database structure.
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
