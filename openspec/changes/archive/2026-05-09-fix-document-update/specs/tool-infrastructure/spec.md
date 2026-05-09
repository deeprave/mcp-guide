## MODIFIED Requirements

### Requirement: Update Documents Tool
The system SHALL provide an MCP tool `update_documents` that updates
documentation files in docroot using the same smart update logic as
`mcp-install update`.

#### Scenario: Tool accepts no arguments
- **WHEN** tool is registered
- **THEN** it accepts no parameters
- **AND** uses session docroot automatically

#### Scenario: Tool works without bound project
- **WHEN** tool is invoked in a session with no bound project
- **AND** global configuration can resolve docroot
- **THEN** the update proceeds using that docroot
- **AND** no `no_project` error is returned

#### Scenario: Tool fails when docroot cannot be resolved
- **WHEN** tool is invoked
- **AND** configuration cannot be read or docroot cannot be resolved
- **THEN** a configuration-related error is returned
- **AND** the tool does not require a bound project as part of that failure path

#### Scenario: No update needed
- **WHEN** tool is invoked
- **AND** `.version` file exists in docroot
- **AND** version matches current package version
- **THEN** success result is returned
- **AND** response indicates that no update was applied
