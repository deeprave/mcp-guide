## ADDED Requirements

### Requirement: Client-aware project root paths
Project selection and root rebinding SHALL interpret supplied root paths through
the configured client-path resolution contract. They SHALL not apply Guide-host
home-directory, user-account, environment-variable, or symlink resolution when
the client filesystem is separate or has not yet been configured.

#### Scenario: Project root on a separate client filesystem
- **WHEN** a separate-filesystem deployment receives an absolute project-root path
- **THEN** it SHALL bind or rebind the project using the lexically normalised client path
- **AND** it SHALL derive configuration identity from that client path without server filesystem resolution

#### Scenario: Percent-encoded local file URI project root
- **WHEN** project selection receives a local `file://` URI with percent-encoded path components
- **THEN** it SHALL percent-decode the URI path before applying client-path validation
- **AND** it SHALL not use the Guide host filesystem to resolve the decoded path

#### Scenario: Unsupported shorthand project root
- **WHEN** project selection receives a user-anchored or relative root path while client filesystems are separate or unconfigured
- **THEN** it SHALL return an invalid-path result directing the caller to provide an absolute client path
