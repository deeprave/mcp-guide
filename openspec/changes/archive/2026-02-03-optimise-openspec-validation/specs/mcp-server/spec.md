## MODIFIED Requirements

### Requirement: OpenSpec Project Validation
The system SHALL validate OpenSpec availability once and persist validation state with version.

#### Scenario: One-time validation with version capture
- **WHEN** OpenSpec feature is enabled for the first time
- **THEN** check `openspec/project.md` exists (do not read content)
- **AND** check OpenSpec command exists
- **AND** request OpenSpec version
- **AND** parse and store version string
- **AND** set validation flag to true
- **AND** never validate again while flag is true

#### Scenario: Skip validated checks
- **WHEN** validation flag is true
- **THEN** skip all OpenSpec validation checks
- **AND** do not request file existence or command location
- **AND** use cached version for feature checks

### Requirement: Version Persistence and Detection
The system SHALL persist OpenSpec version and detect version changes.

#### Scenario: Store version with validation
- **WHEN** OpenSpec validation completes successfully
- **THEN** store version string in project config
- **AND** persist alongside validation flag
- **AND** restore version on session restart

#### Scenario: Detect version changes on startup
- **WHEN** session starts with validated project
- **THEN** check if session version cache is empty
- **AND** compare project version with current OpenSpec version
- **AND** request version if cache empty or version unknown
- **AND** update project config if version changed

#### Scenario: Detect version changes on project switch
- **WHEN** switching to different project
- **THEN** check new project's stored version
- **AND** compare with session version cache
- **AND** request version if different or missing
- **AND** update new project config with current version

### Requirement: Version Comparison
The system SHALL provide semantic version comparison for OpenSpec features.

#### Scenario: Compare versions correctly
- **WHEN** comparing OpenSpec versions
- **THEN** use packaging.version.Version for comparison
- **AND** handle semantic versioning correctly (1.10.2 > 1.9.6)
- **AND** support version prefixes (v1.2.3 or 1.2.3)

#### Scenario: Minimum version checking
- **WHEN** feature requires minimum OpenSpec version
- **THEN** compare current version against minimum
- **AND** return boolean result
- **AND** handle missing version as false
