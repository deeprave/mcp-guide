# Spec Delta

## MODIFIED Requirements

### Requirement: OpenSpec Context Data
The template context system SHALL include OpenSpec project data only from OpenSpec CLI responses run in the session's active worktree when OpenSpec support is enabled. It SHALL not read, request, or derive context from a presumed worktree-relative OpenSpec installation.

#### Scenario: OpenSpec project metadata
- **WHEN** an OpenSpec-enabled template requires project metadata
- **THEN** the context SHALL use data returned by an applicable OpenSpec CLI response
- **AND** SHALL NOT read or request `openspec/project.md`

#### Scenario: Active changes data
- **WHEN** an OpenSpec-enabled template requires active changes
- **THEN** the context SHALL use the result of `openspec list --json`
- **AND** a successful empty changes list SHALL remain valid OpenSpec context

#### Scenario: Specification domains
- **WHEN** an OpenSpec-enabled template requires specification domains
- **THEN** the rendered guidance SHALL obtain them through an OpenSpec CLI command
- **AND** SHALL NOT construct a path beneath a presumed `openspec/specs` directory

#### Scenario: Agent configuration
- **WHEN** an OpenSpec-enabled template requires agent configuration
- **THEN** the context SHALL obtain it through the ordinary project document mechanism
- **AND** SHALL NOT treat OpenSpec store discovery as evidence that a worktree-local `AGENTS.md` exists

### Requirement: On-demand OpenSpec changes context
The template context system SHALL obtain OpenSpec change data only when a rendered feature requires that data. It SHALL evaluate that data in a dynamic context layer on every render, reusing a valid per-session cached `openspec list --json` result rather than issuing another client request or inspecting filesystem metadata.

#### Scenario: First change-data consumer
- **WHEN** an OpenSpec-enabled command or template requires changes data and no valid cached list exists
- **THEN** the system SHALL request `openspec list --json` once
- **AND** SHALL cache the received list for subsequent consumers

#### Scenario: Valid changes cache
- **WHEN** an OpenSpec-enabled command or template requires changes data and the cached list is within its TTL
- **THEN** the system SHALL use the cached list
- **AND** SHALL NOT request another OpenSpec changes list

#### Scenario: Invalidated changes cache
- **WHEN** an OpenSpec-enabled command or template requires changes data and the cached list has expired
- **THEN** the system SHALL request a refreshed changes list
- **AND** SHALL replace the cached list and its acquisition time after receiving the response

#### Scenario: Unusable changes response
- **WHEN** a changes-list response has malformed JSON or does not match the active refresh request ID
- **THEN** the system SHALL leave the cached list and pending refresh unchanged
- **AND** SHALL return a failure that identifies the unusable response

#### Scenario: Forced refresh after a mutation
- **WHEN** a successful OpenSpec mutation directs the agent to `guide://_openspec/list?force`
- **THEN** the list command SHALL request a fresh `openspec list --json` result even when cached changes data remains valid
- **AND** SHALL NOT request a directory listing
