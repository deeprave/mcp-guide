# mcp-discovery Specification

## Purpose
TBD - created by archiving change add-mcp-discovery. Update Purpose after archive.
## Requirements
### Requirement: List Tools Discovery
The system SHALL provide a `list_tools` tool that enumerates all registered MCP tools.

#### Scenario: Enumerate available tools
- **WHEN** `list_tools` is invoked
- **THEN** return a list of all registered tools
- **AND** each tool entry includes name, description, and argument schema
- **AND** response follows Result pattern

### Requirement: List Prompts Discovery
The system SHALL provide a `list_prompts` tool that enumerates all registered MCP prompts.

#### Scenario: Enumerate available prompts
- **WHEN** `list_prompts` is invoked
- **THEN** return a list of all registered prompts
- **AND** each prompt entry includes name and description
- **AND** response follows Result pattern

### Requirement: List Resources Discovery
The system SHALL provide a `list_resources` tool that enumerates all registered MCP resources.

#### Scenario: Enumerate available resources
- **WHEN** `list_resources` is invoked
- **THEN** return a list of all registered resources
- **AND** each resource entry includes URI pattern and description
- **AND** response follows Result pattern

### Requirement: Discovery Tool Registry Access
Discovery tools SHALL access the same registry used by deferred registration to ensure consistency.

#### Scenario: Registry consistency
- **WHEN** a tool is registered via `register_tools()`
- **THEN** it immediately appears in `list_tools` results
- **AND** the registry is the single source of truth for available capabilities

