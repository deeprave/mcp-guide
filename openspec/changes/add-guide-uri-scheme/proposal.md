# Change: Add guide:// URI Scheme Resource Support

## Why

MCP servers can expose resources via the `resources/list` and `resources/read` protocol methods. Currently, mcp-guide only exposes functionality through tools. By implementing the guide:// URI scheme, we enable:

- Direct resource references in agent prompts and workflows
- Declarative resource discovery via `resources/list`
- Standard MCP resource patterns for content access
- Better integration with MCP clients that prefer resources over tools

## What Changes

- Implement MCP `resources/list` handler returning guide:// URIs and templates
- Implement MCP `resources/read` handler for guide:// URI resolution
- Define guide:// URI scheme patterns for categories, collections, documents, and help
- Map URI patterns to existing content retrieval logic (deferred to content tools implementation)

## Impact

- Affected specs: New capability `mcp-resources-guide-scheme`
- Affected code: MCP server initialization, resource handlers
- Dependencies: Content retrieval implementation (to be defined separately)
- No breaking changes - additive feature only
