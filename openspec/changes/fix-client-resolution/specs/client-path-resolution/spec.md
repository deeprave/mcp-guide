## Purpose

Define safe, deployment-configured interpretation of filesystem paths supplied
by an MCP client when that filesystem may differ from the Guide host.

## ADDED Requirements

### Requirement: Deployment-wide client filesystem state
The system SHALL maintain one process-wide client-filesystem sharing state. Its
initial value SHALL be `None`, meaning startup has not yet established whether
client and server filesystems are shared. Startup SHALL explicitly establish the
state as shared or separate independently of the MCP transport in use.

#### Scenario: Client path resolution before startup configuration
- **WHEN** a client path is resolved while the sharing state is `None`
- **THEN** the system SHALL apply the separate-filesystem safety rules
- **AND** it SHALL not expand or resolve the path using the Guide host

#### Scenario: Transport does not determine filesystem sharing
- **WHEN** Guide starts with stdio, HTTP, or HTTPS transport
- **THEN** it SHALL not infer the client-filesystem sharing state from that transport

### Requirement: Shared filesystem client resolution
When the configured client filesystem is shared with the Guide host, the system
SHALL resolve client paths using the host's normal user, environment-variable,
and filesystem resolution rules.

#### Scenario: Shared filesystem user-anchored path
- **WHEN** a shared-filesystem deployment resolves a client path beginning with `~` or `~user`
- **THEN** it SHALL resolve the anchor using the Guide host filesystem

### Requirement: Separate filesystem client resolution
When the configured client filesystem is separate, client paths SHALL remain
lexical client identifiers. The system SHALL require an absolute client path,
normalise lexical path components without filesystem access, and SHALL NOT
expand user anchors, environment variables, or server-visible symlinks.

#### Scenario: Separate filesystem user-anchored path
- **WHEN** a separate-filesystem deployment receives a client path beginning with `~` or `~user`
- **THEN** it SHALL reject the path with an error explaining that an absolute client path is required

#### Scenario: Separate filesystem relative path
- **WHEN** a separate-filesystem deployment receives a relative client path
- **THEN** it SHALL reject the path with an error explaining that an absolute client path is required

#### Scenario: Separate filesystem absolute path
- **WHEN** a separate-filesystem deployment receives an absolute client path containing lexical `.` or `..` components
- **THEN** it SHALL normalise those components without resolving a filesystem path
- **AND** it SHALL preserve the declared identity of any server-visible symlink component
