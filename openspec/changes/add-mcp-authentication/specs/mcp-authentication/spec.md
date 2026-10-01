## Purpose

Define pluggable, provider-backed authentication and scope-based authorisation
for Guide's remote MCP operations without making Guide an identity provider.

## ADDED Requirements

### Requirement: Pluggable remote authentication provider
The system SHALL enable provider-backed remote authorisation only when the
server administrator selects an authentication provider through CLI
configuration. The selected provider SHALL receive only an opaque configuration
reference from Guide and SHALL own credential parsing, validation, external
identity interaction, and scope determination. Guide SHALL NOT issue
credentials, manage accounts, persist credentials, or interpret credential
format or contents.

The remote transport SHALL start and stop the selected provider with its own
lifecycle. Provider startup failure SHALL prevent the enabled remote transport
from serving. When no provider is selected, the system SHALL preserve existing
remote operation behaviour. Stdio SHALL remain trusted and SHALL NOT construct
or invoke an authentication provider.

#### Scenario: No provider is selected
- **WHEN** a server starts without an authentication-provider CLI option
- **THEN** it SHALL not construct a provider
- **AND** remote operations SHALL retain their existing access behaviour

#### Scenario: Provider starts with remote transport
- **WHEN** a server starts a remote transport with a selected provider
- **THEN** it SHALL start the provider before accepting protected operations
- **AND** it SHALL stop the provider when that transport stops

#### Scenario: Provider startup fails
- **WHEN** a selected provider cannot initialise
- **THEN** the remote transport SHALL fail to start
- **AND** it SHALL not serve an endpoint that appears provider-protected

### Requirement: Provider authorisation decisions and handoff
For a protected operation, the system SHALL ask the provider for an
authorisation decision using ephemeral request authentication evidence and an
operation descriptor. The provider SHALL return either an authorised stable
principal with immutable scopes, an unauthenticated decision that may include
an opaque HTTPS handoff/challenge, or a forbidden decision.

Guide SHALL map unauthenticated and forbidden decisions to stable
MCP-compatible results without exposing credential, provider, or policy
details. Guide SHALL NOT redirect an MCP invocation to an interactive login
flow. A provider that needs an interactive flow SHALL own its HTTPS callback or
login routes; a capable client MAY follow its returned handoff before retrying.

#### Scenario: Provider authorises a protected operation
- **WHEN** the provider returns an authorised principal whose scopes satisfy
  the operation requirement
- **THEN** the system SHALL dispatch the operation subject to its existing
  validation and behaviour

#### Scenario: Provider requires authentication
- **WHEN** the provider returns an unauthenticated decision for a protected
  operation
- **THEN** the system SHALL return an authentication-required result
- **AND** it SHALL preserve an opaque handoff when the provider supplied one
- **AND** it SHALL not start an interactive redirect or perform the operation

#### Scenario: Provider denies a scope
- **WHEN** the provider returns a principal without the required scope or a
  forbidden decision
- **THEN** the system SHALL return an insufficient-authorisation result
- **AND** it SHALL not perform the operation

### Requirement: Scope-based operation policy
The system SHALL retain an explicit protected-operation classification for
tools, resources, and prompts. A registration SHALL declare operation kind,
name, optional required scope, and any validated-argument predicate needed for
conditional protection. Operations absent from the classification SHALL retain
their existing behaviour.

- `user` SHALL authorise project administration, including project binding,
  project selection, cloning, and mutation of persisted project configuration,
  plus SQLite document ingestion.
- `admin` SHALL authorise server-wide administration, global feature-flag
  mutation, installed-document updates, and document export.
- `admin` SHALL satisfy a `user` scope requirement.

The classification SHALL apply only while provider-backed policy is active.
It SHALL be enforced after argument validation and before a Session is
created, a project is bound, protected content is read, or an operation has an
effect. The initial protected inventory need not contain a resource or prompt,
but later protected resources and prompts SHALL use this same boundary.

#### Scenario: Admin invokes a user operation
- **WHEN** a provider authorises a caller with the `admin` scope for a
  `user`-protected operation
- **THEN** the system SHALL treat the caller as authorised

#### Scenario: Unprotected operation is called with provider active
- **WHEN** a caller invokes an operation absent from the protected
  classification while provider-backed policy is active
- **THEN** the system SHALL preserve that operation's existing access and
  result behaviour

#### Scenario: Unauthenticated caller invokes a protected operation
- **WHEN** an unauthenticated caller invokes a protected operation while
  provider-backed policy is active
- **THEN** the system SHALL not mint a session, bind a project, persist
  configuration, write documents, read protected content, or emit exports

### Requirement: Provider updates do not replace authorisation checks
The provider MAY asynchronously notify Guide of policy, signing-key, or
revocation changes. The system SHALL apply only provider-approved invalidation
to any cached decisions and SHALL obtain a current provider decision for every
protected operation unless the provider explicitly grants a bounded cache
entry.

#### Scenario: Provider reports a revocation
- **WHEN** the provider notifies the system that an authorisation decision is
  no longer valid
- **THEN** the system SHALL not reuse that decision for a later protected
  operation
