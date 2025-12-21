# Change: Add guide:// URI Scheme Resource Support

## Why

MCP servers can expose resources via the `resources/list` and `resources/read` protocol methods. Currently, mcp-guide only exposes functionality through tools. By implementing the guide:// URI scheme, we enable:

- Direct resource references in agent prompts and workflows
- Declarative resource discovery via `resources/list`
- Standard MCP resource patterns for content access
- Better integration with MCP clients that prefer resources over tools

## What Changes

- Implement MCP resource handler for guide:// URI scheme
- Single URI pattern: `guide://collection/document`
- Direct delegation to existing `internal_get_content` function
- Simple text/markdown responses (no MIME multipart)

## Impact

- Affected specs: New capability `mcp-resources-guide-scheme`
- Affected code: MCP server initialization, resource handlers
- Dependencies: Existing `internal_get_content` from content tools
- No breaking changes - additive feature only

## Design Simplifications

The implementation was simplified from the original proposal:
- Single URI pattern instead of multiple resource types
- No guide://help resource
- No MIME multipart formatting
- Direct delegation to existing content system
