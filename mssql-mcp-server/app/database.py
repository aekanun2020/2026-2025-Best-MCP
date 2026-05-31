"""
Database connection and utilities
"""
import os
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration
DB_SERVER = os.getenv('DB_SERVER', '34.47.90.27')
DB_NAME = os.getenv('DB_NAME', 'Electric')
DB_USER = os.getenv('DB_USER', 'SA')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Passw0rd123456')

# Create SQLAlchemy engine
engine: Optional[Engine] = None

def get_engine() -> Engine:
    """Get or create database engine"""
    global engine
    if engine is None:
        connection_string = f'mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}'
        engine = create_engine(connection_string)
        logger.info("Database engine created")
    return engine

def get_connection() -> Optional[Connection]:
    """Get a database connection"""
    try:
        return get_engine().connect()
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_tables() -> List[str]:
    """Get all table names in the database"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        query = text("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        result = conn.execute(query)
        tables = [row[0] for row in result]
        return tables
    except Exception as e:
        logger.error(f"Error fetching tables: {e}")
        return []
    finally:
        conn.close()

def get_table_schema(table_name: str) -> Optional[List[Dict[str, Any]]]:
    """Get the schema for a specific table"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        query = text(f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
        """)
        
        result = conn.execute(query, {"table_name": table_name})
        columns = []
        
        for row in result:
            col_name, data_type, max_length, is_nullable, default = row
            column_info = {
                "name": col_name,
                "type": data_type,
                "max_length": max_length,
                "nullable": is_nullable == 'YES',
                "default": default
            }
            columns.append(column_info)
            
        return columns
    except Exception as e:
        logger.error(f"Error fetching schema for table {table_name}: {e}")
        return None
    finally:
        conn.close()

def execute_query(query: str) -> Dict[str, Any]:
    """Execute a SQL query and return results"""
    conn = get_connection()
    if not conn:
        return {"error": "Could not connect to the database."}
    
    try:
        # Execute query using pandas for better formatting
        df = pd.read_sql(text(query), conn)
        
        if df.empty:
            return {"result": "Query executed successfully but returned no results."}
        
        # Format result
        result = df.to_string(index=False)
        
        # Limit result size
        if len(result) > 10000:
            result = df.head(100).to_string(index=False)
            result += f"\n\n[Showing only 100 of {len(df)} rows]"
        
        return {"result": result}
    except Exception as e:
        return {"error": f"Error executing query: {str(e)}"}
    finally:
        conn.close()

def get_database_info() -> Dict[str, Any]:
    """Get general information about the database"""
    conn = get_connection()
    if not conn:
        return {"error": "Could not connect to the database."}
    
    info = {
        "database_name": DB_NAME,
        "server": DB_SERVER,
    }
    
    try:
        # Get table count
        tables = get_tables()
        info["table_count"] = len(tables)
        
        # Get database version
        query_version = text("SELECT @@VERSION")
        result = conn.execute(query_version)
        version = result.fetchone()[0]
        info["server_version"] = version
        
        # Get database size
        query_size = text("SELECT SUM(size/128.0) FROM sys.database_files;")
        result = conn.execute(query_size)
        size_mb = result.fetchone()[0]
        info["size_mb"] = round(float(size_mb), 2) if size_mb else None
        
    except Exception as e:
        info["error"] = str(e)
    finally:
        conn.close()
    
    return info


def get_all_relationships() -> List[Dict[str, Any]]:
    """Get all foreign key relationships in the database"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        query = text("""
            SELECT 
                f.name AS foreign_key_name,
                OBJECT_SCHEMA_NAME(f.parent_object_id) + '.' + 
                OBJECT_NAME(f.parent_object_id) AS referencing_table,
                COL_NAME(fc.parent_object_id, fc.parent_column_id) AS referencing_column,
                OBJECT_SCHEMA_NAME(f.referenced_object_id) + '.' + 
                OBJECT_NAME(f.referenced_object_id) AS referenced_table,
                COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
            FROM sys.foreign_keys AS f
            INNER JOIN sys.foreign_key_columns AS fc 
                ON f.object_id = fc.constraint_object_id
            WHERE f.is_ms_shipped = 0
            ORDER BY referencing_table, foreign_key_name
        """)
        
        result = conn.execute(query)
        relationships = []
        
        for row in result:
            relationships.append({
                "foreign_key_name": row[0],
                "referencing_table": row[1],
                "referencing_column": row[2],
                "referenced_table": row[3],
                "referenced_column": row[4]
            })
        
        return relationships
    except Exception as e:
        logger.error(f"Error fetching relationships: {e}")
        return []
    finally:
        conn.close()


def get_loner_tables() -> List[str]:
    """Get tables that have no foreign key relationships (can be queried standalone)"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        query = text("""
            SELECT 
                s.name + '.' + t.name AS [table]
            FROM sys.tables AS t
            INNER JOIN sys.schemas AS s 
                ON t.schema_id = s.schema_id
            INNER JOIN (
                SELECT 
                    schema_name(tab.schema_id) + '.' + tab.name AS tab,
                    COUNT(fk.name) AS fk_cnt
                FROM sys.tables AS tab
                LEFT JOIN sys.foreign_keys AS fk 
                    ON tab.object_id = fk.parent_object_id
                GROUP BY schema_name(tab.schema_id), tab.name
            ) fks 
                ON s.name + '.' + t.name = fks.tab
            INNER JOIN (
                SELECT 
                    schema_name(tab.schema_id) + '.' + tab.name AS tab,
                    COUNT(fk.name) AS ref_cnt
                FROM sys.tables AS tab
                LEFT JOIN sys.foreign_keys AS fk 
                    ON tab.object_id = fk.referenced_object_id
                GROUP BY schema_name(tab.schema_id), tab.name
            ) refs 
                ON s.name + '.' + t.name = refs.tab
            WHERE fks.fk_cnt + refs.ref_cnt = 0
            ORDER BY [table]
        """)
        
        result = conn.execute(query)
        loner_tables = [row[0] for row in result]
        
        return loner_tables
    except Exception as e:
        logger.error(f"Error fetching loner tables: {e}")
        return []
    finally:
        conn.close()


def get_relationship_graph() -> Dict[str, Any]:
    """Get comprehensive relationship graph for the database"""
    relationships = get_all_relationships()
    loner_tables = get_loner_tables()
    
    # Build graph structure
    graph = {
        "has_relationships": len(relationships) > 0,
        "relationship_count": len(relationships),
        "loner_table_count": len(loner_tables),
        "foreign_keys": relationships,
        "loner_tables": loner_tables,
        "query_hints": {}
    }
    
    # Add query hints based on relationships
    if len(relationships) > 0:
        graph["query_hints"]["has_joins"] = True
        graph["query_hints"]["join_syntax"] = "Use proper JOIN syntax with ON clause"
        graph["query_hints"]["fk_query"] = "SELECT * FROM sys.foreign_keys to view all relationships"
    else:
        graph["query_hints"]["has_joins"] = False
        graph["query_hints"]["note"] = "No foreign key constraints found. Tables can be queried independently."
    
    if len(loner_tables) > 0:
        graph["query_hints"]["standalone_tables"] = f"{len(loner_tables)} table(s) can be queried without joins"
    
    return graph

# Cache for tables and schemas
class DatabaseCache:
    """Simple cache for database metadata"""
    def __init__(self):
        self.tables: Optional[List[str]] = None
        self.schemas: Dict[str, List[Dict[str, Any]]] = {}
        self.relationship_graph: Optional[Dict[str, Any]] = None
    
    def refresh(self):
        """Refresh the cache"""
        logger.info("Refreshing database cache...")
        self.tables = get_tables()
        self.schemas = {}
        for table in self.tables:
            schema = get_table_schema(table)
            if schema:
                self.schemas[table] = schema
        
        # Cache relationship graph
        self.relationship_graph = get_relationship_graph()
        
        logger.info(f"Cache refreshed. Found {len(self.tables)} tables, "
                   f"{self.relationship_graph['relationship_count']} relationships, "
                   f"{self.relationship_graph['loner_table_count']} loner tables.")
    
    def get_tables(self) -> List[str]:
        """Get cached tables"""
        if self.tables is None:
            self.refresh()
        return self.tables or []
    
    def get_schema(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached schema for a table"""
        if table_name not in self.schemas:
            schema = get_table_schema(table_name)
            if schema:
                self.schemas[table_name] = schema
        return self.schemas.get(table_name)
    
    def get_relationship_graph(self) -> Dict[str, Any]:
        """Get cached relationship graph"""
        if self.relationship_graph is None:
            self.relationship_graph = get_relationship_graph()
        return self.relationship_graph

# Initialize cache
db_cache = DatabaseCache()
