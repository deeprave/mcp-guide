## Purpose

Define optional caller authentication and scope-based authorisation for MCP
operations that can alter Guide projects, server state, or document output.

## ADDED Requirements

### Requirement: Optional MCP caller authentication
The system SHALL support an optional authentication configuration for HTTP and
HTTPS MCP transports. When authentication is not configured, it SHALL preserve
existing unauthenticated behaviour for every operation not classified as
protected. When authentication is configured, the system SHALL derive an
authenticated caller identity and its granted scopes before evaluating a
protected operation. Stdio transport SHALL be trusted and SHALL NOT require
authentication or scope checks for any operation.

#### Scenario: Authentication is not configured
- **WHEN** an HTTP or HTTPS deployment has no authentication configuration
- **THEN** an unauthenticated caller MAY invoke an unprotected operation
- **AND** a protected operation SHALL fail without performing its side effect

#### Scenario: Stdio invocation is trusted
- **WHEN** a caller invokes any MCP operation through stdio
- **THEN** the system SHALL not require caller credentials or scopes
- **AND** it SHALL apply the operation's existing validation and behaviour

#### Scenario: Valid caller credentials are presented
- **WHEN** an HTTP or HTTPS caller presents valid configured credentials
- **THEN** the system SHALL associate the resulting identity and scopes with
  that request
- **AND** the credentials SHALL NOT be exposed through a Session, tool result,
  log message, or error response

#### Scenario: Invalid caller credentials are presented
- **WHEN** an HTTP or HTTPS caller presents invalid, expired, or malformed
  credentials
- **THEN** the system SHALL reject the request as unauthenticated
- **AND** it SHALL NOT run a protected operation or disclose which credential
  component failed validation

### Requirement: Scope-based protected operations
The system SHALL protect operations by the following scope policy:

- `user` SHALL authorise project administration, including project binding,
  project selection, cloning, and mutation of a project's persisted
  configuration, plus SQLite document ingestion.
- `admin` SHALL authorise server-wide administration, global feature-flag
  mutation, installed-document updates, and document export.
- `admin` SHALL satisfy a `user` scope requirement.

The system SHALL retain an explicit protected-operation classification at the
HTTP(S) application boundary. Operations not in that classification SHALL not
require authentication solely because they do not require a bound project.

#### Scenario: User administers a project
- **WHEN** a caller authenticated with the `user` scope invokes a protected
  project-administration operation
- **THEN** the system SHALL permit the operation subject to its existing input
  and project validation

#### Scenario: User invokes a server-administration operation
- **WHEN** a caller authenticated only with the `user` scope invokes an
  `admin`-protected operation
- **THEN** the system SHALL return an authorisation failure
- **AND** it SHALL not perform the operation's side effect

#### Scenario: Admin invokes a project-administration operation
- **WHEN** a caller authenticated with the `admin` scope invokes a
  `user`-protected operation
- **THEN** the system SHALL treat the caller as authorised for that operation

#### Scenario: Unauthenticated caller invokes a protected operation
- **WHEN** an unauthenticated caller invokes an operation classified as
  protected
- **THEN** the system SHALL return a consistent authentication-required result
- **AND** it SHALL not bind a project, persist configuration, write documents,
  or emit exported content

#### Scenario: Unauthenticated caller invokes an unprotected operation
- **WHEN** an unauthenticated caller invokes an operation not classified as
  protected
- **THEN** the system SHALL preserve that operation's existing access and
  result behaviour

#### Scenario: File-content callback does not request document ingestion
- **WHEN** an unauthenticated HTTP(S) caller invokes `send_file_content`
  without document-ingestion metadata
- **THEN** the system SHALL preserve its existing callback behaviour
- **AND** it SHALL not require the `user` scope solely for that callback
