# packaging Specification Delta

## MODIFIED Requirements

### Requirement: Script Entry Points
Scripts SHALL be accessible via uvx and direct installation methods.

#### Scenario: guide-agent-install via uvx
- **WHEN** running `uvx --from mcp-guide guide-agent-install -l`
- **THEN** script SHALL list all available agent configurations
- **AND** agent configuration files SHALL be accessible from package

#### Scenario: mcp-install via uvx
- **WHEN** running `uvx --from mcp-guide mcp-install`
- **THEN** script SHALL execute successfully
- **AND** all required package data SHALL be accessible

#### Scenario: Package data inclusion
- **WHEN** building package distribution
- **THEN** agent configuration files SHALL be included
- **AND** all script dependencies SHALL be accessible
- **AND** path resolution SHALL work across installation methods

#### Scenario: Consistent behavior
- **WHEN** scripts are run via uvx, pip install, or direct execution
- **THEN** behavior SHALL be identical
- **AND** all configuration files SHALL be found
- **AND** no empty output due to missing files
