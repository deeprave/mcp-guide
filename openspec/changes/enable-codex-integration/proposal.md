# Change: Enable Codex Integration via Command URIs

## Why

OpenAI Codex CLI fully supports custom URI schemes but does not support direct MCP prompts. While `guide://collection/document` works for content retrieval, Codex cannot execute commands like `:project` or `:status` that are available via the guide prompt.

This creates a UX gap where Codex users cannot access command functionality that other agents can use through prompts.

## What Changes

Enable command execution through the `guide://` URI scheme using underscore-prefixed paths:

- `guide://_command` - Execute command with no arguments
- `guide://_command/arg1/arg2` - Execute command with positional arguments
- `guide://_command?kwarg=value` - Execute command with keyword arguments
- `guide://_openspec/list?verbose=true` - Example: openspec list command with verbose flag

The underscore prefix distinguishes commands from collections/categories and is already reserved for system use.

**Prerequisites:**
- Add underscore prefix validation to `collection_add` and `collection_change` to prevent collision with command URIs (currently only categories have this validation)

## Impact

**Affected specs:**
- `mcp-resources-guide-scheme` - Add command URI support
- `collection-tools` - Add underscore prefix validation (prerequisite)

**Affected code:**
- `src/mcp_guide/resources.py` - Update resource handler to detect and route command URIs
- `src/mcp_guide/uri_parser.py` - Extend to parse command URIs with args/kwargs
- `src/mcp_guide/tools/tool_collection.py` - Add underscore validation (prerequisite)
- `src/mcp_guide/discovery/commands.py` - Command cache used for URI parsing

**Benefits:**
- Codex users gain full command access via URIs
- Consistent interface across all MCP clients
- No breaking changes to existing `guide://collection/document` pattern
