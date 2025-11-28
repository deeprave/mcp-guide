# Implementation Tasks

## 1. Result Pattern Implementation
- [ ] 1.1 Create Result class in mcp_core (if not exists)
- [ ] 1.2 Add to_json_str() method for MCP responses
- [ ] 1.3 Define standard error types for content retrieval

## 2. Content Retrieval Core
- [ ] 2.1 Implement pattern matching logic (glob-based)
- [ ] 2.2 Implement single match formatter (plain markdown)
- [ ] 2.3 Implement multiple match formatter (MIME multipart)
- [ ] 2.4 Add metadata extraction for MIME parts

## 3. Tool Implementation
- [ ] 3.1 Implement get_content tool with argument schema
- [ ] 3.2 Implement get_category_content tool with argument schema
- [ ] 3.3 Implement get_collection_content tool with argument schema
- [ ] 3.4 Add session integration for project context

## 4. Error Handling
- [ ] 4.1 Define error types (not_found, invalid_pattern, etc.)
- [ ] 4.2 Add agent instructions for each error type
- [ ] 4.3 Implement Result.failure() responses
- [ ] 4.4 Test error message clarity

## 5. Tool Registration
- [ ] 5.1 Register tools with MCP server
- [ ] 5.2 Define tool schemas per ADR-008 conventions
- [ ] 5.3 Add tool descriptions and examples
- [ ] 5.4 Validate tool schemas

## 6. Testing
- [ ] 6.1 Unit tests for pattern matching
- [ ] 6.2 Unit tests for content formatting
- [ ] 6.3 Integration tests for each tool
- [ ] 6.4 Test error cases and instructions
- [ ] 6.5 Test MIME multipart parsing

## 7. Documentation
- [ ] 7.1 Document tool usage and examples
- [ ] 7.2 Document pattern syntax
- [ ] 7.3 Document MIME multipart format
- [ ] 7.4 Add troubleshooting guide
