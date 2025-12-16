# list-category-files Implementation Tasks

## Task List

1. **Add list_category_files tool specification**
   - Add requirement to category-tools spec
   - Define tool arguments schema
   - Define success/failure response formats
   - Add validation scenarios

2. **Implement list_category_files tool**
   - Add tool function to tool_category.py
   - Use existing discover_category_files with `**/*` pattern
   - Format output as 2-column (path, size)
   - Strip .mustache extension from basenames
   - Return Result pattern response

3. **Add tool argument validation**
   - Validate category name exists
   - Use existing category name validation
   - Handle session management errors

4. **Add unit tests**
   - Test successful file listing
   - Test category not found error
   - Test no session error
   - Test empty directory
   - Test template file basename stripping
   - Test scan limits respected

5. **Add integration tests**
   - Test with real category directory
   - Test with mixed file types
   - Test with subdirectories
   - Verify 2-column output format

6. **Update tool registration**
   - Ensure tool is registered in MCP server
   - Verify tool appears in tool list

## Validation
- All tests pass
- Tool validates successfully with openspec
- Tool appears in MCP tool list
- Manual testing shows expected output format
