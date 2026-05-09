## MODIFIED Requirements

### Requirement: Autoupdate Feature Flag
The system SHALL provide a global feature flag `autoupdate` that controls
automatic update prompting at startup.

#### Scenario: Global flag only
- **WHEN** flag is set at global level
- **THEN** flag is accepted and stored
- **AND** flag value is boolean (true/false)

#### Scenario: Boolean values are normalised
- **WHEN** `autoupdate` is set using an accepted boolean-like string value
- **THEN** the stored value is normalised using the standard boolean normaliser
- **AND** `"true"`, `"on"`, and `"enabled"` are stored as `true`
- **AND** `"false"`, `"off"`, and `"disabled"` are stored as `false`

#### Scenario: Project-level flag rejected
- **WHEN** flag is set at project level
- **THEN** validation error is returned
- **AND** error message states "autoupdate must be global flag only"

#### Scenario: Flag resolution defaults to enabled
- **WHEN** `McpUpdateTask` checks `autoupdate`
- **AND** no global flag value is present
- **THEN** startup update prompting is treated as enabled

#### Scenario: Explicit false disables prompting
- **WHEN** `McpUpdateTask` checks `autoupdate`
- **AND** the global flag value is `false`
- **THEN** startup update prompting is disabled

#### Scenario: Explicit true enables prompting
- **WHEN** `McpUpdateTask` checks `autoupdate`
- **AND** the global flag value is `true`
- **THEN** startup update prompting is enabled
