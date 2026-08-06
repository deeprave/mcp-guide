## ADDED Requirements

### Requirement: Relay fallback after direct-access evaluation
The system SHALL retain agent filesystem relay as the default and fallback path for every direct-access-eligible operation.

#### Scenario: Direct access is unavailable
- **WHEN** a filesystem-derived operation is requested without confirmed direct access
- **THEN** the system SHALL preserve the existing agent-relay request and ingestion behavior

#### Scenario: Direct read fails
- **WHEN** a confirmed direct filesystem read fails or returns stale data
- **THEN** the system SHALL revoke direct access for that operation's session
- **AND** SHALL request the required data through the existing relay mechanism

### Requirement: Relay prompt suppression after successful direct reads
The system SHALL not request an agent to relay data that the server has successfully obtained through confirmed direct filesystem access.

#### Scenario: Direct data is current
- **WHEN** a workflow or OpenSpec task successfully obtains current data directly
- **THEN** the system SHALL suppress prompts, instructions, and reminders that request `send_file_content` or equivalent relay of that data

#### Scenario: Direct data is not current
- **WHEN** direct data is absent, unreadable, or no longer fresh
- **THEN** the system SHALL not suppress the relay prompt or reminder
