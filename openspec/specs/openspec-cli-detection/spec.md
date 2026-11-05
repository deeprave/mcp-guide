# openspec-cli-detection Specification

## Purpose
Defines how Guide detects the OpenSpec CLI's availability and version in a single request/response round trip, and how the agent is told why this information is requested and where it is stored.

## Requirements

### Requirement: Gated by the openspec feature flag
The system SHALL only initiate OpenSpec CLI detection when the `openspec` feature flag is enabled for the active project. When the flag is not enabled, the system SHALL NOT send any detection instruction.

#### Scenario: Flag disabled
- **WHEN** the `openspec` feature flag is not enabled for the active project
- **THEN** no CLI detection instruction is sent

#### Scenario: Flag enabled
- **WHEN** the `openspec` feature flag is enabled for the active project
- **AND** no recent detection result exists
- **THEN** a CLI detection instruction is sent

### Requirement: Single combined detection instruction
The system SHALL request OpenSpec CLI version in one instruction, requiring the agent to run `openspec --version` and report the result in one tool call. The instruction SHALL state that the information refreshes the machine-wide OpenSpec validation and version state.

#### Scenario: One instruction covers both location and version
- **WHEN** the system requests OpenSpec CLI detection
- **THEN** the agent SHALL be asked to obtain only the `openspec --version` result rather than the historical location-and-version probe
- **AND** SHALL report it in one tool call

#### Scenario: Instruction explains purpose and storage
- **WHEN** the agent receives the detection instruction
- **THEN** the instruction SHALL state that the result refreshes OpenSpec-dependent feature availability
- **AND** SHALL state that the result is stored in the global `openspec-state` feature flag

### Requirement: Combined result reporting uses a structured synthetic path
The system SHALL receive the version-refresh result via the `send_file_content` tool using the synthetic path `.openspec-info.json`, with JSON content carrying the version command result. The system SHALL NOT add OpenSpec-specific fields to the generic `send_command_location` tool.

#### Scenario: Combined report accepted
- **WHEN** the agent sends file content at path `.openspec-info.json`
- **THEN** the system SHALL parse the reported version command result

#### Scenario: Generic command-location tool remains unmodified
- **WHEN** any command's location is reported via `send_command_location`
- **THEN** its arguments remain limited to `command` and `location`
- **AND** no OpenSpec-specific field is present on that tool

### Requirement: Distinguishes not-found, found-without-version, and found-with-version
The system SHALL distinguish a failed version command, an unparseable version result, and a parseable semantic version. `openspec-state.validated` SHALL be `true` only when a semantic version was successfully parsed.

#### Scenario: CLI not found
- **WHEN** the version command cannot run successfully
- **THEN** `openspec-state.validated` SHALL be set to `false`
- **AND** `openspec-state.version` SHALL not be set

#### Scenario: CLI found but version unparseable
- **WHEN** the version command succeeds
- **AND** no semantic version pattern can be parsed from its result
- **THEN** `openspec-state.validated` SHALL be set to `false`
- **AND** `openspec-state.version` SHALL not be set

#### Scenario: CLI found with parseable version
- **WHEN** a semantic version pattern is parsed from the version command result
- **THEN** `openspec-state.validated` SHALL be set to `true`
- **AND** `openspec-state.version` SHALL be set to the parsed version
- **AND** the system SHALL NOT request repository-asset detection as a consequence

### Requirement: openspec-state remains a global-only feature flag
The system SHALL continue to store OpenSpec CLI detection results in `openspec-state` as a global feature flag, not as a project-level override.

#### Scenario: Result is global
- **WHEN** OpenSpec CLI detection completes for any project
- **THEN** the resulting `openspec-state` value is visible identically across all projects
