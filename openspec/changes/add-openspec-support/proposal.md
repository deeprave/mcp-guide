# Change: Add OpenSpec MCP Integration Support

## Why
Enable MCP-Guide to provide OpenSpec workflow capabilities through the Model Context Protocol, making spec-driven development accessible to any MCP-compatible AI assistant. This eliminates the need for tool-specific OpenSpec integrations and provides universal access to OpenSpec workflows across Claude.ai, GitHub Copilot, Amazon Q, and other MCP-enabled platforms.

## What Changes
- Add conditional OpenSpec detection and integration (requires feature-flags)
- Implement MCP tools for OpenSpec workflow operations
- Provide MCP resources for OpenSpec project state queries
- Add MCP prompts for guided spec-driven development workflows
- Integrate OpenSpec data into existing template context hierarchy

## Impact
- Affected specs: mcp-server, template-context
- Affected code: MCP server implementation, template rendering system
- **BREAKING**: None - feature is conditional and additive
- Dependencies: Requires feature-flags implementation (currently in openspec/ideas)
