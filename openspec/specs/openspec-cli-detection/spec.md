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
The system SHALL request OpenSpec CLI location and version in one instruction, requiring the agent to perform one shell check and report the combined result in a single tool call, rather than requesting location and version as two separate round trips.

The instruction SHALL state, in second person, why the information is requested (to determine whether OpenSpec-dependent features are available, since some may be gated by CLI version) and where the reported result is stored (the project's `openspec-state` feature flag).

#### Scenario: One instruction covers both location and version
- **WHEN** the system requests OpenSpec CLI detection
- **THEN** the agent is asked to determine both the CLI's location and its version in one shell invocation
- **AND** the agent reports both together in a single tool call

#### Scenario: Instruction explains purpose and storage
- **WHEN** the agent receives the detection instruction
- **THEN** the instruction states why the check is requested
- **AND** the instruction states that the result is stored in the `openspec-state` feature flag

### Requirement: Combined result reporting uses a structured synthetic path
The system SHALL receive the combined detection result via the `send_file_content` tool using the synthetic path `.openspec-info.json`, with JSON content carrying both the CLI location and version, consistent with this handler's existing JSON-content synthetic paths (`.openspec-changes.json`, `.openspec-status.json`). The system SHALL NOT add OpenSpec-specific fields to the generic `send_command_location` tool.

#### Scenario: Combined report accepted
- **WHEN** the agent sends file content at path `.openspec-info.json`
- **THEN** the system parses both location and version from that single JSON report

#### Scenario: Generic command-location tool remains unmodified
- **WHEN** any command's location is reported via `send_command_location`
- **THEN** its arguments remain limited to `command` and `location`
- **AND** no OpenSpec-specific field is present on that tool

### Requirement: Distinguishes not-found, found-without-version, and found-with-version
The system SHALL distinguish three outcomes from the combined report: the CLI was not found; the CLI was found but its version could not be parsed; and the CLI was found with a parseable semantic version. Each outcome SHALL update the `openspec-state` feature flag consistently with the existing `OpenSpecState`/`parse_openspec_state`/`serialise_openspec_state` semantics: `validated` SHALL be `true` only when a semantic version was successfully parsed.

#### Scenario: CLI not found
- **WHEN** the combined report indicates the CLI was not found
- **THEN** `openspec-state.validated` is set to `false`
- **AND** `openspec-state.version` is not set

#### Scenario: CLI found but version unparseable
- **WHEN** the combined report indicates the CLI was found
- **AND** no semantic version pattern can be parsed from the reported output
- **THEN** `openspec-state.validated` is set to `false`

#### Scenario: CLI found with parseable version
- **WHEN** the combined report indicates the CLI was found
- **AND** a semantic version pattern is parsed from the reported output
- **THEN** `openspec-state.validated` is set to `true`
- **AND** `openspec-state.version` is set to the parsed version
- **AND** OpenSpec project-structure detection is requested, consistent with existing post-validation behavior

### Requirement: openspec-state remains a global-only feature flag
The system SHALL continue to store OpenSpec CLI detection results in `openspec-state` as a global feature flag, not as a project-level override.

#### Scenario: Result is global
- **WHEN** OpenSpec CLI detection completes for any project
- **THEN** the resulting `openspec-state` value is visible identically across all projects
