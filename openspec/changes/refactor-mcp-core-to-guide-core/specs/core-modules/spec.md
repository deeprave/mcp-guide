## MODIFIED Requirements

### Requirement: Core Module Import Paths
The system SHALL provide core functionality through the `mcp_guide.core` module namespace instead of the separate `mcp_core` module.

#### Scenario: Import core functionality
- **WHEN** code needs to import core functionality
- **THEN** it SHALL use `from mcp_guide.core import ...` instead of `from mcp_core import ...`

#### Scenario: Package installation
- **WHEN** users install the mcp-guide package
- **THEN** all functionality SHALL be available under the single `mcp_guide` module tree
