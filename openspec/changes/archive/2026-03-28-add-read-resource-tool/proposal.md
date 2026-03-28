# Change: Add read_resource tool for guide:// URI access

## Why

AI agents cannot call MCP `resources/read` directly — they can only invoke tools. The existing `guide://` resource scheme is fully functional but inaccessible to agents unless they know the specific `get_content` expression that maps to a given URI. A `read_resource` tool lets agents follow any `guide://` reference encountered in instructions, content, or error messages.

Additionally, agents like OpenAI Codex CLI cannot execute commands via MCP prompts. By supporting command URIs (`guide://_command`) in the same tool, agents gain full command access through a single entry point.

## What Changes

- Add a `read_resource` MCP tool that accepts a `guide://` URI and returns the resource content or command output
- Add a `uri_parser` module to parse `guide://` URIs into content or command requests
- Add underscore prefix validation to collection tools (prerequisite — prevents collision with command URIs)
- The tool delegates to existing `internal_get_content` for content URIs and `handle_command` for command URIs

## Impact

- Affected specs: mcp-resources-guide-scheme
- Affected code: tool registration layer, collection validation, new uri_parser module, new tool_resource module
