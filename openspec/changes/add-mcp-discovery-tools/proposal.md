# Change: Add MCP Discovery Tools

## Why

Discovery tools enable agents to enumerate available MCP capabilities (tools, prompts, resources) for introspection and capability discovery.

## What Changes

- Implement `list_prompts` tool (enumerate available prompts)
- Implement `list_resources` tool (enumerate available resources)
- Implement `list_tools` tool (enumerate available tools)
- Return Result pattern responses
- Follow tool conventions (ADR-008)

## Impact

- Affected specs: New capability `mcp-discovery-tools`
- Affected code: New tools module, MCP introspection
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008), category/collection tools
- Breaking changes: None (new tools)
