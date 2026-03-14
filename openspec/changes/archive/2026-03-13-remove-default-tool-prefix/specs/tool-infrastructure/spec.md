## MODIFIED Requirements

### Requirement: Environment Configuration
The system SHALL configure MCP_TOOL_PREFIX early in mcp_guide startup.

#### Scenario: Default prefix configuration
- **WHEN** mcp_guide starts and MCP_TOOL_PREFIX not set
- **THEN** default tool prefix is empty string (no prefix)
- **AND** tools are registered without any prefix

#### Scenario: User-provided prefix preserved
- **WHEN** mcp_guide starts and MCP_TOOL_PREFIX is set to a non-empty value
- **THEN** existing value is used as the tool prefix
- **AND** tools are registered with that prefix
