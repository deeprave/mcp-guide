# Change: Add read_resource tool for guide:// URI access

## Why

AI agents cannot call MCP `resources/read` directly — they can only invoke tools. The existing `guide://` resource scheme is fully functional but inaccessible to agents unless they know the specific `get_content` expression that maps to a given URI. A `read_resource` tool would let agents follow any `guide://` reference encountered in instructions, content, or error messages.

## What Changes

- Add a `read_resource` MCP tool that accepts a `guide://` URI and returns the resource content
- The tool delegates to the existing guide:// resource handler infrastructure

## Impact

- Affected specs: mcp-resources-guide-scheme
- Affected code: tool registration layer, guide resource handler
