## ADDED Requirements

### Requirement: Bounded machine-wide OpenSpec version checks
The OpenSpec task SHALL use the global OpenSpec state to check the installed
OpenSpec CLI version at most once in each rolling 24-hour period on a computer.

#### Scenario: First or expired version check
- **WHEN** global `openspec.checked` is null or at least 24 hours old
- **AND** an OpenSpec version check is needed
- **THEN** the task SHALL request an OpenSpec version check

#### Scenario: Recent version check is reused
- **WHEN** global `openspec.checked` is less than 24 hours old
- **THEN** the task SHALL NOT request another OpenSpec version check
- **AND** it SHALL use the stored global validation and version values

#### Scenario: Completed version check updates global state
- **WHEN** an OpenSpec version-check response has been processed
- **THEN** the task SHALL set global `openspec.checked` to the current UTC Unix
  timestamp as a float
- **AND** it SHALL persist the parsed version and validation result globally

#### Scenario: Invalid version-check response is bounded
- **WHEN** an OpenSpec version-check response cannot establish a valid version
- **THEN** the task SHALL persist `validated=false` and `version=null`
- **AND** it SHALL still update global `openspec.checked`
