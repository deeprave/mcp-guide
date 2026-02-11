# tool-registration Specification

## Purpose
TBD - created by archiving change add-mcp-discovery. Update Purpose after archive.
## Requirements
### Requirement: Deferred Tool Registration
The system SHALL provide a `@toolfunc()` decorator that stores tool metadata without performing MCP registration at import time.

#### Scenario: Tool definition without side effects
- **WHEN** a tool module is imported
- **THEN** no MCP registration occurs
- **AND** tool metadata is stored in registry

### Requirement: Explicit Registration Function
The system SHALL provide a `register_tools(mcp)` function that registers all collected tools with an MCP server instance.

#### Scenario: Server initialization with explicit registration
- **WHEN** `register_tools(mcp)` is called during server creation
- **THEN** all tools in registry are registered with the MCP server
- **AND** tools become available for invocation

