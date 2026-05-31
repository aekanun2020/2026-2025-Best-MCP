# Implementation Plan: Fix MCP Server 500 Errors

## Overview

This implementation plan addresses the 500 Internal Server Errors in the PyRAGDoc MCP server by fixing async/await compatibility with Qdrant, adding service validation, and implementing comprehensive error handling. The tasks are organized to fix the core issues first, then add validation and testing.

## Tasks

- [x] 1. Fix async/await compatibility in Storage Service
  - [x] 1.1 Wrap Qdrant client calls in initialize() method with asyncio.to_thread
    - Wrap `client.get_collections()` call
    - Wrap `client.create_collection()` call
    - Wrap `client.get_collection()` call
    - Add import for asyncio at the top of the method
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.2 Wrap Qdrant client calls in recreate_collection() method with asyncio.to_thread
    - Wrap `client.delete_collection()` call
    - Wrap `client.create_collection()` call
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.3 Wrap Qdrant client calls in add_document() method with asyncio.to_thread
    - Wrap `client.upsert()` call
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.4 Wrap Qdrant client calls in add_documents() method with asyncio.to_thread
    - Wrap `client.upsert()` call in the batch loop
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.5 Wrap Qdrant client calls in search() method with asyncio.to_thread
    - Wrap `client.search()` call
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.6 Wrap Qdrant client calls in list_sources() method with asyncio.to_thread
    - Wrap `client.scroll()` call
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.7 Wrap Qdrant client calls in delete_documents() method with asyncio.to_thread
    - Wrap `client.delete()` call
    - _Requirements: 1.1, 1.2_
  
  - [ ]* 1.8 Write property test for async wrapper preservation
    - **Property 1: Async Wrapper Preservation**
    - **Validates: Requirements 1.2**
    - Generate random valid inputs for Qdrant operations
    - Verify wrapped calls preserve return values and exceptions
    - Run minimum 100 iterations

- [x] 2. Add service validation to MCP server tools
  - [x] 2.1 Create validate_services() helper function in app/mcp_server.py
    - Check if embedding_service is None
    - Check if storage_service is None
    - Return descriptive error message or None
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.2 Add service validation to search_documentation() tool
    - Call validate_services() at the start of the function
    - Return error message if validation fails
    - Log error at ERROR level
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.3 Add service validation to add_documentation() tool
    - Call validate_services() at the start of the function
    - Return error message if validation fails
    - Log error at ERROR level
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.4 Add service validation to list_sources() tool
    - Call validate_services() at the start of the function
    - Return error message if validation fails
    - Log error at ERROR level
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.5 Add service validation to add_directory() tool
    - Call validate_services() at the start of the function
    - Return error message if validation fails
    - Log error at ERROR level
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 2.6 Write property test for service validation
    - **Property 2: Service Validation Before Execution**
    - **Validates: Requirements 2.1, 2.2**
    - Generate random tool calls with various service states
    - Verify tools check services before execution
    - Verify error messages are returned when services are None
    - Run minimum 100 iterations

- [x] 3. Checkpoint - Test basic functionality
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Enhance error handling in message processing pipeline
  - [x] 4.1 Review and enhance error handling in process_mcp_message()
    - Ensure all tool execution paths are wrapped in try-except
    - Verify exceptions are logged with full stack traces using exc_info=True
    - Ensure JSON-RPC error responses are properly formatted
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 4.2 Add specific error handling for tools/call method
    - Wrap tool execution in try-except block
    - Log exceptions at ERROR level with full stack trace
    - Return JSON-RPC error response with code -32603
    - Include error message in the data field
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 4.3 Write property test for error response format consistency
    - **Property 3: Error Response Format Consistency**
    - **Validates: Requirements 3.2, 5.1**
    - Generate random exceptions during message processing
    - Verify all exceptions result in valid JSON-RPC error responses
    - Verify error response structure is consistent
    - Run minimum 100 iterations
  
  - [ ]* 4.4 Write property test for no unhandled exceptions
    - **Property 4: No Unhandled Exceptions**
    - **Validates: Requirements 3.3, 5.4**
    - Generate random error conditions in tool execution
    - Verify no exceptions propagate as HTTP 500 errors
    - Verify all errors are logged and converted to responses
    - Run minimum 100 iterations

- [x] 5. Add detailed logging throughout the system
  - [x] 5.1 Add INFO level logging for tool calls in app/mcp_server.py
    - Log tool name and arguments when tools are called
    - Already partially implemented, verify all tools have logging
    - _Requirements: 4.1_
  
  - [x] 5.2 Add DEBUG level logging for Qdrant operations in storage.py
    - Log operation name and key parameters before each Qdrant call
    - Add to all methods that call Qdrant client
    - _Requirements: 4.2_
  
  - [x] 5.3 Verify ERROR level logging for all exceptions
    - Ensure all exception handlers log at ERROR level with exc_info=True
    - Review all try-except blocks in mcp_server.py, main.py, and storage.py
    - _Requirements: 4.3_

- [ ] 6. Add integration tests for complete request-response flow
  - [ ]* 6.1 Write integration test for search_documentation with uninitialized services
    - Test that proper error response is returned
    - Verify no HTTP 500 errors occur
    - _Requirements: 2.1, 2.2, 5.4_
  
  - [ ]* 6.2 Write integration test for search_documentation with Qdrant errors
    - Mock Qdrant client to raise exceptions
    - Verify proper error response is returned
    - Verify error message includes Qdrant error details
    - _Requirements: 3.2, 5.3_
  
  - [ ]* 6.3 Write integration test for add_directory with file processing errors
    - Test with invalid directory paths
    - Test with files that cause processing errors
    - Verify proper error responses
    - _Requirements: 3.1, 3.2_

- [ ] 7. Final checkpoint - Comprehensive testing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- The fix prioritizes core functionality (async/await and service validation) before adding comprehensive testing
