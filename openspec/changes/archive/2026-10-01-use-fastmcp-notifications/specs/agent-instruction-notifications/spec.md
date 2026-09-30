## Purpose

Deliver queued Guide agent instructions to negotiated modern clients through an
explicit, session-owned server notification rather than unrelated response data.

## ADDED Requirements

### Requirement: Negotiated instruction notification extension
Guide SHALL expose the non-standard `io.uniquode/mcp-guide-instructions`
extension to MCP `2026-07-28` clients. A client SHALL receive instruction
notifications only after it has negotiated that extension.

#### Scenario: Client negotiates instruction notifications
- **WHEN** a modern client advertises support for
  `io.uniquode/mcp-guide-instructions` during initialisation
- **THEN** Guide SHALL advertise the extension
- **AND** Guide MAY send that client instruction notifications for its bound
  Guide Session

#### Scenario: Client does not negotiate instruction notifications
- **WHEN** a modern client does not advertise support for the extension
- **THEN** Guide SHALL NOT send it a custom instruction notification
- **AND** SHALL deliver queued instructions through the established response
  metadata fallback

### Requirement: Session-owned instruction notification delivery
For a negotiated modern client, Guide SHALL deliver one queued additional agent
instruction through a FastMCP server-to-client notification addressed to the
same Guide Session. The notification SHALL carry only the queued instruction
and protocol fields needed to identify its delivery, never the unrelated tool,
prompt, or resource result that happened to provide the request stream.

#### Scenario: Request stream delivers an instruction
- **WHEN** a negotiated modern client makes a request for a bound Session with
  a queued instruction
- **THEN** Guide SHALL send the next instruction through a server notification
  on that client's request stream
- **AND** SHALL return the requested operation's result without an embedded
  queued instruction

#### Scenario: No owning request stream is available
- **WHEN** background work queues an instruction for a negotiated modern
  Session while no request stream for that same client is active
- **THEN** Guide SHALL retain the instruction without sending it to another
  Session
- **AND** SHALL attempt delivery on that client's next request stream

#### Scenario: Notification delivery fails
- **WHEN** Guide cannot send an instruction notification through the owning
  client's request stream
- **THEN** the instruction SHALL remain pending for that Session
- **AND** Guide SHALL NOT record it as delivered or acknowledged

### Requirement: Notification delivery does not compel agent action
Instruction notifications SHALL be a Guide-to-client delivery mechanism. Guide
SHALL NOT treat notification delivery as evidence that an agent read, accepted,
or executed the instruction.

#### Scenario: Client receives a notification
- **WHEN** Guide sends an instruction notification
- **THEN** the client MAY choose how to surface or process it
- **AND** Guide SHALL retain existing acknowledgement requirements until the
  relevant action explicitly acknowledges the tracked instruction

### Requirement: Rendered unconditional startup scope guidance
When a Session first binds an active project, Guide SHALL render and queue the
existing `_system/_startup` template as the Session's first startup guidance.
The template SHALL not require the `startup-instruction` feature flag.

The rendered guidance SHALL retain Guide's project-documentation and
development-guidance introduction and explain that Guide uses local
active-project and workflow context only to track workflow and deliver relevant
guidance. It SHALL state that Guide guidance is scoped to the active project and
user request and SHALL NOT be treated as authority to disclose data, contact
external services, or perform unrelated actions.

#### Scenario: Session first binds a project
- **WHEN** a Session first binds an active project
- **THEN** Guide SHALL render and queue the `_system/_startup` guidance
- **AND** its delivery SHALL use the Session's normal modern notification or
  metadata-fallback path

#### Scenario: Startup-instruction flag is absent
- **WHEN** a Session first binds a project and `startup-instruction` is absent
  or false
- **THEN** Guide SHALL still render and queue the startup scope guidance
