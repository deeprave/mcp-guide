## ADDED Requirements

### Requirement: Update Documents Tool
The system SHALL provide an MCP tool `update_documents` that updates documentation files in docroot using the same smart update logic as `mcp-install update`.

#### Scenario: Update needed - version differs
- **WHEN** tool is invoked
- **AND** `.version` file exists in docroot
- **AND** version differs from current package version
- **THEN** update proceeds using smart update logic
- **AND** `.version` is updated to current package version
- **AND** `.original.zip` is created/updated
- **AND** success result with statistics is returned

#### Scenario: Update needed - version missing
- **WHEN** tool is invoked
- **AND** `.version` file does not exist in docroot
- **THEN** update proceeds (treat as old installation)
- **AND** `.version` is created with current package version
- **AND** `.original.zip` is created/updated
- **AND** success result with statistics is returned

#### Scenario: No update needed
- **WHEN** tool is invoked
- **AND** `.version` file exists in docroot
- **AND** version matches current package version
- **THEN** error result is returned
- **AND** message states "documents do not require updating"

#### Scenario: Exclusive access via locking
- **WHEN** tool is invoked
- **THEN** docroot is ensured to exist via `mkdir(parents=True, exist_ok=True)`
- **AND** lock path is `docroot / ".update"` (creates `.update.lock`)
- **AND** `lock_update(lock_path, _perform_update, docroot, archive_path)` is used
- **AND** lock is automatically cleaned up on completion or error

#### Scenario: Tool accepts no arguments
- **WHEN** tool is registered
- **THEN** it accepts no parameters
- **AND** uses session docroot automatically

#### Scenario: Lock shared with mcp-install script
- **WHEN** both MCP tool and mcp-install script use update functionality
- **THEN** both use same lock path `docroot / ".update"`
- **AND** concurrent operations wait for lock
- **AND** lock file is `{docroot}/.update.lock`
