# Transport Security Specification

**Dependencies:** None (foundational spec)

## ADDED Requirements

### Requirement: Docroot-Restricted Access
The system SHALL restrict all document operations to within the configured docroot directory.

#### Scenario: Read access within docroot
- **WHEN** client requests document within docroot
- **THEN** access is allowed on any transport

#### Scenario: Access outside docroot
- **WHEN** client requests document outside docroot
- **THEN** access is denied regardless of transport

### Requirement: Write Operation Security
The system SHALL require HTTPS with authentication for write operations on network transports.

#### Scenario: Write on STDIO
- **WHEN** transport is STDIO
- **THEN** write operations are allowed (local trusted access)

#### Scenario: Write on HTTP without auth
- **WHEN** transport is HTTP/SSE/WebSocket without HTTPS and authentication
- **THEN** write operations are denied
