# Implementation Tasks

**Approval gate**: COMPLETED

## 1. URI Pattern Definition
- [x] 1.1 Define guide:// URI structure and semantics - Simplified to guide://collection/document
- [x] 1.2 Document URI patterns in spec - Updated specification with simplified design
- [x] 1.3 Define resource vs template distinction - Using template resources only

## 2. MCP Resource Handlers
- [x] 2.1 Implement `resources/list` handler - Returns URI template guide://{collection}/{document}
- [x] 2.2 Implement `resources/read` handler - Delegates to internal_get_content
- [x] 2.3 Add URI parsing and routing logic - Implemented in uri_parser.py
- [x] 2.4 Integrate with content retrieval - Direct delegation to internal_get_content

## 3. Help Resource
- [x] 3.1 ~~Create guide://help content generator~~ - REMOVED: Simplified design excludes help resource
- [x] 3.2 ~~Document URI patterns and usage~~ - REMOVED: Simplified design excludes help resource
- [x] 3.3 ~~Include examples and common patterns~~ - REMOVED: Simplified design excludes help resource

## 4. Testing
- [x] 4.1 Unit tests for URI parsing - Comprehensive tests in test_uri_parser.py
- [x] 4.2 Integration tests for resource handlers - Tests in test_resource_handlers.py
- [x] 4.3 Test resource discovery via resources/list - Covered in integration tests
- [x] 4.4 Test content retrieval via resources/read - Covered in integration tests

## 5. Documentation
- [x] 5.1 Update README with resource usage examples - Added brief section with reference to guide://_workflow/guide-uri-scheme.md
- [x] 5.2 Document URI patterns and semantics - Created templates/_workflow/guide-uri-scheme.md with detailed documentation
- [x] 5.3 ~~Add troubleshooting guide~~ - NOT NEEDED: Error messages are clear enough

## Implementation Notes

**Design Changes**: The implementation was simplified from the original proposal:
- Removed guide://help resource for cleaner design
- Single URI pattern: guide://collection/document
- Direct delegation to existing content system
- No complex routing or multi-resource aggregation

**Files Modified**:
- `src/mcp_guide/uri_parser.py` - URI parsing utility
- `src/mcp_guide/resources.py` - MCP resource handlers
- `src/mcp_guide/server.py` - Resource handler registration
- `tests/unit/test_uri_parser.py` - Unit tests
- `tests/integration/test_resource_handlers.py` - Integration tests
