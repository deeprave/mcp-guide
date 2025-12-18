# list-category-files Implementation Tasks

## Task List

- [x] 0. Fix dict-based configuration compatibility issues
  - [x] 0.1 Fix category lookup in tool_category.py to use dict access
  - [x] 0.2 Fix category lookup in tool_content.py to use dict access
  - [x] 0.3 Fix category lookup in tool_collection.py to use dict access
  - [x] 0.4 Fix category lookup in tool_project.py clone functionality
  - [x] 0.5 Fix pattern expansion to support basename with extensions
  - [x] 0.6 Fix file validation to allow legitimate dot-prefixed paths
  - [x] 0.7 Fix symlink path resolution in file discovery
  - [x] 0.8 Test category content retrieval works with symlinked docroot

- [x] 1. Add list_category_files tool specification
  - [x] 1.1 Add requirement to category-tools spec
  - [x] 1.2 Define tool arguments schema
  - [x] 1.3 Define success/failure response formats
  - [x] 1.4 Add validation scenarios

- [x] 2. Implement list_category_files tool
  - [x] 2.1 Add tool function to tool_category.py
  - [x] 2.2 Use existing discover_category_files with `**/*` pattern
  - [x] 2.3 Format output as 2-column (path, size)
  - [x] 2.4 Strip .mustache extension from basenames
  - [x] 2.5 Return Result pattern response

- [x] 3. Add tool argument validation
  - [x] 3.1 Validate category name exists
  - [x] 3.2 Use existing category name validation
  - [x] 3.3 Handle session management errors

- [x] 4. Add unit tests
  - [x] 4.1 Test successful file listing
  - [x] 4.2 Test category not found error
  - [x] 4.3 Test no session error
  - [x] 4.4 Test empty directory
  - [x] 4.5 Test template file basename stripping
  - [x] 4.6 Test scan limits respected

- [x] 5. Add integration tests
  - [x] 5.1 Test with real category directory
  - [x] 5.2 Test with mixed file types
  - [x] 5.3 Test with subdirectories
  - [x] 5.4 Verify 2-column output format

- [x] 6. Update tool registration
  - [x] 6.1 Ensure tool is registered in MCP server
  - [x] 6.2 Verify tool appears in tool list

## Validation
- [x] All tests pass
- [x] Tool validates successfully with openspec
- [x] Tool appears in MCP tool list
- [x] Manual testing shows expected output format
