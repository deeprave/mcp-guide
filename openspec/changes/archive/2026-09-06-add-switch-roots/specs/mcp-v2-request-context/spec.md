## MODIFIED Requirements

### Requirement: FastMCP Session-ID Cross-Request Binding

The system SHALL use FastMCP's minted, principal-validated session_id as the
explicit cross-request identity for a modern interaction. That public ID SHALL
select runtime's current bound Guide Session while the server is running, not
promise the same concrete Session object throughout the interaction.

A project switch SHALL retain the validated public ID and existing protocol
connection while replacing the Guide Session behind it. It SHALL NOT mint or
retire a FastMCP ID for an internal project replacement. Retained legacy
connection identity SHALL continue selecting the current Guide Session without
requiring clients to adopt a new session argument.

Guide SHALL persist only project configuration. It SHALL NOT persist or restore
root bindings, active selection, instructions, task state or rendering caches
across a server restart.

#### Scenario: Valid session-ID round trip
- **WHEN** an interaction binds with set_project and obtains a FastMCP session ID
- **THEN** the common result adapter SHALL return that ID in its standard structured result
- **AND** later requests supplying the validated ID SHALL resolve the current bound Guide Session

#### Scenario: Modern project replacement preserves the public ID
- **GIVEN** a modern interaction has a validated public ID
- **WHEN** switch_project succeeds
- **THEN** its result SHALL retain that same ID
- **AND** a following request with the ID SHALL use the replacement's project
- **AND** no new protocol session or token SHALL be required

#### Scenario: Retained legacy client switches project
- **GIVEN** a retained legacy connection uses its public connection identity
- **WHEN** it successfully switches projects
- **THEN** its next request SHALL resolve the replacement using the same connection identity
- **AND** it SHALL NOT be required to replay a newly introduced identifier

#### Scenario: Unknown or invalid session ID
- **WHEN** a request supplies an ID that FastMCP does not validate for the principal
- **THEN** the system SHALL reject it without creating a replacement Guide Session
- **AND** it SHALL NOT select a project or deliver instructions using the invalid ID
- **AND** it SHALL return the existing distinct invalid-session guidance to discard the ID and begin with set_project

#### Scenario: MCP server restart
- **WHEN** the server restarts
- **THEN** prior unbound, bound and expiring Guide state SHALL be discarded
- **AND** a new interaction SHALL bind before project-bound behaviour is available
- **AND** persisted project configuration SHALL remain available for that binding

## ADDED Requirements

### Requirement: Session Establishment Protocol Logging

The system SHALL log the negotiated MCP protocol revision and available client
name/version once when a validated Guide interaction is first established.
Internal project replacement under the same public ID SHALL NOT count as a new
interaction establishment. The establishment log SHALL NOT include public
session IDs or client filesystem paths.

#### Scenario: Protocol is recorded at establishment
- **WHEN** a modern or retained legacy interaction is first established
- **THEN** the negotiated protocol revision and available client name/version SHALL be recorded once

#### Scenario: Internal replacement is not a new establishment
- **GIVEN** the interaction's establishment has already been logged
- **WHEN** a project switch replaces the Guide Session without changing its public ID
- **THEN** a duplicate establishment log SHALL NOT be emitted

#### Scenario: Request-local work is not interaction establishment
- **GIVEN** a modern request has no validated or minted public interaction ID
- **WHEN** it uses an ephemeral unbound Session
- **THEN** it SHALL NOT emit an interaction-establishment log
