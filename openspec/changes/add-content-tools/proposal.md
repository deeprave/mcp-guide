# Change: Add Content Retrieval Tools

## Why

Content retrieval is the core functionality of mcp-guide. Currently, the implementation is incomplete and doesn't follow the Result pattern (ADR-003) or tool conventions (ADR-008). We need standardized tools for accessing category and collection content with:

- Consistent error handling using Result pattern
- Clear argument schemas per tool conventions
- Support for pattern-based content matching
- Proper formatting for single vs multiple matches
- Agent-friendly error instructions

## What Changes

### Core Tools
- Implement `get_category_content` tool (category-specific access)
- Implement `get_collection_content` tool (collection-specific access)
- Implement `get_content` tool (unified category/collection access)

### Content Retrieval
- Glob pattern matching for file discovery
- File reading and content extraction
- Support optional pattern parameter for content filtering
- Format single matches as plain markdown
- Format multiple matches as MIME multipart

### Template Discovery (IMPLEMENTED)
- **Template Discovery** (IMPLEMENTED in GUIDE-33): Finding `.mustache` files
  - Templates named as `{basename}.{ext}.mustache` (e.g., `doc.md.mustache`)
  - Pattern matching includes both regular files and templates (e.g., `*.md` matches `*.md.mustache`)
  - Template precedence: prefer non-template over template when both exist
  - FileInfo includes `basename` field (filename without `.mustache` extension)
  - Pattern expansion: search both `pattern` and `pattern.mustache`
  - Deduplication: group by basename, prefer non-template

**Note**: Template rendering and context resolution moved to separate `template-support` feature.

### Error Handling
- Return Result pattern responses with proper error handling
- Add agent instructions for error cases
- Specific error types: not_found, no_matches, invalid_pattern, no_session

## Impact

- Affected specs: New capability `content-tools`
- Affected code: New tools module, content retrieval, MCP server tool registration
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008)
- Breaking changes: None (new tools)
- Phased implementation: Core content retrieval → Collection-based retrieval
- External dependency: Collection management tools (add-collection-tools) must be implemented before get_collection_content
- Template support: Handled by separate `template-support` feature
