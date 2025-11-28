# Change: Add Content Retrieval Tools

## Why

Content retrieval is the core functionality of mcp-guide. Currently, the implementation is incomplete and doesn't follow the Result pattern (ADR-003) or tool conventions (ADR-008). We need standardized tools for accessing category and collection content with:

- Consistent error handling using Result pattern
- Clear argument schemas per tool conventions
- Support for pattern-based content matching
- Proper formatting for single vs multiple matches
- Agent-friendly error instructions

## What Changes

- Implement `get_content` tool (unified category/collection access)
- Implement `get_category_content` tool (category-specific access)
- Implement `get_collection_content` tool (collection-specific access)
- Return Result pattern responses with proper error handling
- Support optional pattern parameter for content filtering
- Format single matches as plain markdown
- Format multiple matches as MIME multipart
- Add agent instructions for error cases

## Impact

- Affected specs: New capability `content-tools`
- Affected code: New tools module, MCP server tool registration
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008)
- Breaking changes: None (new tools)
- Future expansion: Document-specific arguments when document functionality is implemented
