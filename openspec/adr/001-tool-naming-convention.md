# ADR-001: Tool Naming Convention

**Date:** 2025-11-25
**Status:** Decided
**Deciders:** Development Team

## Context

MCP servers provide tools to AI agents, but some agents like kiro/Amazon Q don't automatically prefix tool names with the server name. This creates potential naming conflicts when multiple MCP servers are used together, and makes it unclear which server provides which tools and often the agent will arbitrarily exclude one or other of the tools. Prefixed tools also make it clear to the agent the intended purpose of the tool and suggest the context in which it should be used.

## Decision

Use namespaced tool names with `guide_` prefix for all tools provided by this MCP server.

## Rationale

- **Disambiguation**: Clear identification of tools from this server vs others
- **Consistency**: All tools follow the same naming pattern
- **Flexibility**: Configurable prefix via `MCP_TOOL_PREFIX` environment variable
- **User Experience**: Agents can easily identify guide-specific tools

## Implementation

- Custom tool decorator with configurable prefix
- Default prefix: `guide` (configurable via `MCP_TOOL_PREFIX` environment variable)
- Tool names follow pattern: `{prefix}_{action}` or `{prefix}_{resource}_{action}`

## Consequences

**Positive:**
- Clear tool identification and disambiguation
- Consistent naming across all tools
- Configurable for different deployment scenarios

**Negative:**
- Slightly longer tool names
- Additional configuration complexity

## Status

Decided - to be implemented in mcp-guide v2.
