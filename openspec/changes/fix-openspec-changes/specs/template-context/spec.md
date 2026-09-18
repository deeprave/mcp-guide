## ADDED Requirements

### Requirement: On-demand OpenSpec changes context
The template context system SHALL obtain OpenSpec change data only when a
rendered feature requires that data. It SHALL evaluate that data in a dynamic
context layer on every render, reusing a valid per-session cached changes list
rather than issuing another client request.

#### Scenario: First change-data consumer
- **WHEN** an OpenSpec-enabled command or template requires changes data and
  no valid cached list exists
- **THEN** the system SHALL request `openspec list --json` once
- **AND** SHALL cache the received list for subsequent consumers

#### Scenario: Valid changes cache
- **WHEN** an OpenSpec-enabled command or template requires changes data and
  the cached list is within its TTL and matches the observed
  `openspec/changes` directory modification time
- **THEN** the system SHALL use the cached list
- **AND** SHALL NOT request another OpenSpec changes list

#### Scenario: Invalidated changes cache
- **WHEN** an OpenSpec-enabled command or template requires changes data and
  the cached list has expired or the observed `openspec/changes` directory
  modification time differs from the cached value
- **THEN** the system SHALL request a refreshed changes list
- **AND** SHALL replace the cached list and its cache metadata after receiving
  the response

#### Scenario: Forced refresh after a mutation
- **WHEN** a successful OpenSpec mutation directs the agent to
  `guide://_openspec/list?force`
- **THEN** the list command SHALL request a fresh directory listing and
  `openspec list --json` even when cached changes data remains valid
