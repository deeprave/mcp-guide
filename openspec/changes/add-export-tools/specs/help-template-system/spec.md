## ADDED Requirements

### Requirement: Export Command Organization
The system SHALL organize export commands under `_commands/export/` directory structure.

#### Scenario: Export command structure
- **WHEN** export commands are discovered
- **THEN** they are located at `_commands/export/add.mustache`, `_commands/export/list.mustache`, `_commands/export/remove.mustache`
- **AND** `add.mustache` has alias 'export' for backward compatibility
- **AND** commands are accessible as `:export/add`, `:export/list`, `:export/remove`, and `:export`

### Requirement: Export List Command
The system SHALL provide an `:export/list` command that displays formatted export information.

#### Scenario: Display formatted exports
- **WHEN** `:export/list` command is invoked
- **THEN** agent is instructed to call `list_exports` tool
- **AND** result is formatted using `_system/_exports-format.mustache` template
- **AND** formatted output is displayed to user

#### Scenario: Command with filter
- **WHEN** `:export/list <glob>` command is invoked with a glob pattern
- **THEN** agent passes the glob to `list_exports` tool
- **AND** only matching exports are displayed

### Requirement: Export Remove Command
The system SHALL provide an `:export/remove` command that removes export tracking entries.

#### Scenario: Remove export tracking
- **WHEN** `:export/remove <expression> [pattern]` command is invoked
- **THEN** agent is instructed to call `remove_export` tool with the provided arguments
- **AND** success or error message is displayed

### Requirement: Export List Template
The system SHALL provide a `_system/_exports-format.mustache` template for formatting export lists.

#### Scenario: Format export list
- **WHEN** template receives export data array
- **THEN** each export is displayed with expression, pattern (if present), path, and timestamp
- **AND** stale exports are visually indicated with a warning marker
- **AND** empty list shows "No exports found" message
