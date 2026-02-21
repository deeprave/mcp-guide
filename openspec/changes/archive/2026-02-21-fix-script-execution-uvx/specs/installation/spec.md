## MODIFIED Requirements

### Requirement: Console Script Entry Points

The system SHALL provide console script entry points that work with both local execution and uvx remote execution.

#### Scenario: Local execution with uv run
- **WHEN** user runs `uv run mcp-install --help`
- **THEN** the script executes successfully and displays help

#### Scenario: Remote execution with uvx
- **WHEN** user runs `uvx --from mcp-guide mcp-install --help`
- **THEN** the script executes successfully and displays help

#### Scenario: All console scripts work
- **WHEN** user runs any console script (mcp-install, osvcheck, guide-agent-install)
- **THEN** the script imports modules correctly and executes
