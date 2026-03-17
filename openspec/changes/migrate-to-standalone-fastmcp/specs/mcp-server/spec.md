## ADDED Requirements
### Requirement: Standalone FastMCP Dependency
The system SHALL depend on the standalone `fastmcp` package (PrefectHQ) rather than the vendored FastMCP bundled within the `mcp` SDK.

#### Scenario: Import from standalone package
- **WHEN** any module requires FastMCP or Context types
- **THEN** imports use `from fastmcp import FastMCP, Context`
- **AND** imports do NOT use `from mcp.server.fastmcp import ...`

#### Scenario: Transitive MCP SDK access
- **WHEN** low-level MCP protocol types are needed
- **THEN** they remain accessible via `mcp.*` imports
- **AND** the `mcp` package is available as a transitive dependency of `fastmcp`

#### Scenario: Server instructions via public API
- **WHEN** server instructions need to be set or updated
- **THEN** the system uses FastMCP's public API
- **AND** does NOT access private attributes of the FastMCP server instance

## MODIFIED Requirements
### Requirement: Server Configuration Options
The system SHALL support command-line options for docroot and config directory.

#### Scenario: Override docroot on server startup
- **WHEN** server starts with -d or --docroot option
- **THEN** server uses specified docroot
- **AND** config file is updated if docroot differs

#### Scenario: Override config directory on server startup
- **WHEN** server starts with -c or --configdir option
- **THEN** server loads config from specified directory
- **AND** creates config there if it doesn't exist

#### Scenario: Transport settings separated from server definition
- **WHEN** the server is constructed
- **THEN** transport-specific settings (host, port) are NOT passed to the FastMCP constructor
- **AND** transport configuration is provided at run time
