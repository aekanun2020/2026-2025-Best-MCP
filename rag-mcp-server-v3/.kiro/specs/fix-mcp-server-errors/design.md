# Design Document: Fix MCP Server 500 Errors

## Overview

This design addresses the 500 Internal Server Errors in the PyRAGDoc MCP server by fixing async/await compatibility issues with the Qdrant client, adding comprehensive error handling throughout the message processing pipeline, and implementing service initialization validation. The solution ensures graceful error handling and detailed logging for debugging.

## Architecture

The fix involves three main layers:

1. **Storage Layer** (pyragdoc/core/storage.py): Wrap all synchronous Qdrant client calls with `asyncio.to_thread` to make them properly async-compatible
2. **Tool Layer** (app/mcp_server.py): Add service initialization checks before tool execution
3. **Message Processing Layer** (main.py): Enhance error handling in the message pipeline to catch and properly format all exceptions

### Data Flow

```
Client Request → FastAPI Endpoint → process_mcp_message()
                                    ↓
                            Service Validation
                                    ↓
                            Tool Execution (with error handling)
                                    ↓
                            Qdrant Operations (async-wrapped)
                                    ↓
                            Response or Error (JSON-RPC format)
```

## Components and Interfaces

### 1. Storage Service (QdrantService)

**Modified Methods:**
- `initialize()`: Wrap `client.get_collections()`, `client.create_collection()`, `client.get_collection()` with `asyncio.to_thread`
- `add_document()`: Wrap `client.upsert()` with `asyncio.to_thread`
- `add_documents()`: Wrap `client.upsert()` with `asyncio.to_thread`
- `search()`: Wrap `client.search()` with `asyncio.to_thread`
- `list_sources()`: Wrap `client.scroll()` with `asyncio.to_thread`
- `delete_documents()`: Wrap `client.delete()` with `asyncio.to_thread`
- `recreate_collection()`: Wrap `client.delete_collection()` and `client.create_collection()` with `asyncio.to_thread`

**Pattern:**
```python
# Before (synchronous call treated as async)
result = self.client.some_method(args)

# After (properly wrapped)
import asyncio
result = await asyncio.to_thread(self.client.some_method, args)
```

### 2. MCP Server Tools (app/mcp_server.py)

**Service Validation Helper:**
```python
def validate_services() -> Optional[str]:
    """Validate that required services are initialized.
    
    Returns:
        Error message if validation fails, None if successful
    """
    if embedding_service is None:
        return "Service not initialized: embedding_service"
    if storage_service is None:
        return "Service not initialized: storage_service"
    return None
```

**Modified Tool Functions:**
Each tool function will check services before execution:
- `search_documentation()`
- `add_documentation()`
- `list_sources()`
- `add_directory()`

**Pattern:**
```python
async def search_documentation(query: str, limit: int = 5) -> str:
    try:
        # Validate services
        error = validate_services()
        if error:
            logger.error(error)
            return error
        
        logger.info(f"Searching documentation with query: {query}")
        # ... rest of implementation
    except Exception as e:
        error_msg = f"Error searching documentation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
```

### 3. Message Processing Pipeline (main.py)

**Enhanced Error Handling in process_mcp_message():**

The function already has a try-except block, but we'll ensure:
1. All tool execution paths are wrapped in try-except
2. Errors are logged with full stack traces
3. JSON-RPC error responses are properly formatted
4. Service validation errors are caught and returned as proper error responses

**Error Response Format:**
```python
{
    "jsonrpc": "2.0",
    "id": message_id,
    "error": {
        "code": -32603,  # Internal error
        "message": "Internal error",
        "data": str(exception)
    }
}
```

## Data Models

No changes to data models are required. The existing `DocumentChunk`, `SearchResult`, and `DocumentMetadata` models remain unchanged.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Async Wrapper Preservation

*For any* Qdrant client method call, wrapping it with `asyncio.to_thread` should preserve the return value and exception behavior of the original synchronous call.

**Validates: Requirements 1.2**

### Property 2: Service Validation Before Execution

*For any* tool call, if either embedding_service or storage_service is None, the tool should return an error message without attempting to execute the tool logic.

**Validates: Requirements 2.1, 2.2**

### Property 3: Error Response Format Consistency

*For any* exception that occurs during message processing, the system should return a valid JSON-RPC error response with code -32603 and the error message in the data field.

**Validates: Requirements 3.2, 5.1**

### Property 4: No Unhandled Exceptions

*For any* tool call or message processing operation, exceptions should be caught and converted to error responses rather than propagating as HTTP 500 errors.

**Validates: Requirements 3.3, 5.4**

## Error Handling

### Error Categories

1. **Service Initialization Errors**: Services not available when tool is called
   - Detection: Check if service variables are None
   - Response: Return descriptive error message
   - Logging: ERROR level with service name

2. **Qdrant Operation Errors**: Database operations fail
   - Detection: Catch exceptions from Qdrant client
   - Response: Wrap in StorageError with descriptive message
   - Logging: ERROR level with full stack trace

3. **Tool Execution Errors**: Errors during tool logic
   - Detection: Catch exceptions in tool functions
   - Response: Return error message string
   - Logging: ERROR level with full stack trace

4. **Message Processing Errors**: Errors in MCP protocol handling
   - Detection: Catch exceptions in process_mcp_message()
   - Response: JSON-RPC error response
   - Logging: ERROR level with full stack trace

### Error Propagation

```
Tool Error → Logged → Error String Returned → Wrapped in JSON-RPC Response → Sent to Client
Storage Error → Logged → StorageError Raised → Caught by Tool → Error String Returned
Service Validation Error → Logged → Error String Returned → Wrapped in JSON-RPC Response
```

## Testing Strategy

### Unit Tests

Unit tests will verify specific error scenarios and edge cases:

1. **Service Validation Tests**:
   - Test tool calls with None services
   - Test tool calls with initialized services
   - Verify error messages match expected format

2. **Async Wrapper Tests**:
   - Test that asyncio.to_thread preserves return values
   - Test that asyncio.to_thread preserves exceptions
   - Test with various Qdrant operations

3. **Error Response Tests**:
   - Test JSON-RPC error response format
   - Test error codes are correct
   - Test error messages are descriptive

### Property-Based Tests

Property-based tests will verify universal correctness properties across many generated inputs:

1. **Property Test for Async Wrapper Preservation** (Property 1):
   - Generate random valid inputs for Qdrant operations
   - Verify wrapped calls return same results as unwrapped calls
   - Verify exceptions are preserved

2. **Property Test for Service Validation** (Property 2):
   - Generate random tool call scenarios with various service states
   - Verify tools always check services before execution
   - Verify error messages are returned when services are None

3. **Property Test for Error Response Format** (Property 3):
   - Generate random exceptions during message processing
   - Verify all exceptions result in valid JSON-RPC error responses
   - Verify error response structure is consistent

4. **Property Test for Exception Handling** (Property 4):
   - Generate random error conditions in tool execution
   - Verify no exceptions propagate as HTTP 500 errors
   - Verify all errors are logged and converted to responses

**Configuration**: Each property test should run a minimum of 100 iterations to ensure comprehensive coverage through randomization.

**Tagging**: Each property test must include a comment tag referencing the design document property:
- `# Feature: fix-mcp-server-errors, Property 1: Async Wrapper Preservation`
- `# Feature: fix-mcp-server-errors, Property 2: Service Validation Before Execution`
- `# Feature: fix-mcp-server-errors, Property 3: Error Response Format Consistency`
- `# Feature: fix-mcp-server-errors, Property 4: No Unhandled Exceptions`

### Integration Tests

Integration tests will verify the complete request-response flow:

1. Test search_documentation with uninitialized services
2. Test search_documentation with Qdrant connection errors
3. Test add_directory with file processing errors
4. Test message processing with malformed requests

### Testing Approach

- **Unit tests** focus on specific examples, edge cases, and error conditions
- **Property tests** verify universal properties across all inputs through randomization
- Together they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness
