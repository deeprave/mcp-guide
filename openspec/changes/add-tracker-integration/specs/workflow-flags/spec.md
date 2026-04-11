## ADDED Requirements

### Requirement: Tracker Feature Flag
The system SHALL support a `tracker` project feature flag that configures integration with an external issue tracker.

#### Scenario: Tracker flag with string value
- **WHEN** `tracker` flag is set to a string such as `github`
- **THEN** the system SHALL treat it as the tracker type with default connection settings

#### Scenario: Tracker flag with dict value
- **WHEN** `tracker` flag is set to a dict with `type` and `project` or `repo` keys
- **THEN** the system SHALL use the specified type and connection parameters for resolution

#### Scenario: Unsupported tracker type
- **WHEN** `tracker` flag is set to an unrecognised type
- **THEN** the system SHALL emit a validation error naming the unsupported value
- **AND** workflow SHALL continue to function without tracker resolution

#### Scenario: Tracker flag absent
- **WHEN** `tracker` flag is not set
- **THEN** tracker resolution SHALL be disabled
- **AND** all workflow commands SHALL behave exactly as without tracker support

### Requirement: Tracker Authentication
When a tracker is configured, the system SHALL resolve authentication credentials from environment variables without storing secrets in flag configuration.

#### Scenario: GitHub token resolution
- **WHEN** tracker type is `github`
- **THEN** the system SHALL look up the token from `GITHUB_TOKEN` environment variable

#### Scenario: Linear token resolution
- **WHEN** tracker type is `linear`
- **THEN** the system SHALL look up the token from `LINEAR_API_KEY` environment variable

#### Scenario: Jira token resolution
- **WHEN** tracker type is `jira`
- **THEN** the system SHALL look up credentials from `JIRA_BASE_URL`, `JIRA_USER`, and `JIRA_API_TOKEN` environment variables

#### Scenario: Missing credentials
- **WHEN** required environment variables are absent
- **THEN** tracker resolution SHALL be skipped with a clear informational message
- **AND** the workflow command SHALL complete using the manually supplied argument
