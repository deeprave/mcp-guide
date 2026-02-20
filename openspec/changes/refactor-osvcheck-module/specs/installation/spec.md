## MODIFIED Requirements

### Requirement: Development Dependencies

The system SHALL support development-only tools via dependency groups.

#### Scenario: Install osvcheck as dev dependency

GIVEN mcp-guide project with dev dependencies
WHEN `uv sync` is executed
THEN osvcheck SHALL be installed from PyPI
AND osvcheck command SHALL be available in development environment
AND osvcheck SHALL NOT be included in production distributions

## REMOVED Requirements

### Requirement: Console Script Registration

**Reason**: osvcheck moved to separate project
**Migration**: Add osvcheck to dev dependencies instead

The system SHALL register osvcheck as a console script.

#### Scenario: Register osvcheck command

GIVEN pyproject.toml with project.scripts section
WHEN package is installed
THEN osvcheck command SHALL be available
AND osvcheck SHALL execute scripts.osvcheck:main
