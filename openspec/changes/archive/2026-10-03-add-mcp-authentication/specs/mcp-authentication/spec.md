## Purpose

Define optional, pluggable authentication for remote Guide MCP operations
without making Guide an identity provider or interpreting credentials.

## ADDED Requirements

### Requirement: Pluggable remote authentication provider
The system SHALL select at most one authentication provider with
`--auth-provider <provider>`, resolving the name from the
`mcp_guide.auth_providers` entry-point group. Provider-specific deployment
configuration SHALL be owned by that provider, including its own environment,
files, or external services. Guide SHALL NOT offer a provider-config CLI
argument.

The selected provider SHALL start and stop with a remote HTTP(S) transport.
Provider startup failure SHALL prevent that remote transport from serving.
Stdio SHALL reject `--auth-provider`. Guide
SHALL NOT issue credentials, manage accounts, persist credentials, or parse
credential formats or contents.

#### Scenario: No provider is selected
- **WHEN** a server starts without `--auth-provider`
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

### Requirement: Opaque request authorisation and handoff
For each remote request, Guide SHALL supply the provider with ephemeral request
evidence. The provider SHALL return `UserAuthorisation`: a set of scope names
and an optional opaque HTTPS authentication handoff. Guide SHALL use `user` for
ordinary protected operations and `admin` for administrative operations;
`admin` SHALL also satisfy `user` operations.

Authenticated state SHALL mean the presence of `user` or `admin`, with
unauthenticated state its complement. Future capability scopes SHALL require
`user` alongside them unless `admin` is present.

Guide SHALL map absence of both `user` and `admin` to `not_authorised` (HTTP 401
semantics), and insufficient required scope to `forbidden` (HTTP 403 semantics),
without exposing tokens, principals, provider
details, or credential data. Guide SHALL NOT redirect an MCP invocation to an
interactive login flow. A provider requiring interactive authentication SHALL
own its HTTPS callback or login routes; a capable client MAY follow the returned
handoff before retrying.
These codes SHALL be returned inside MCP Result payloads; this mapping SHALL NOT
change HTTP transport status codes or introduce HTTP authentication challenges.

#### Scenario: Provider supplies user access
- **WHEN** the provider returns `UserAuthorisation` containing `user`
- **THEN** the system SHALL dispatch a user-protected operation subject to its
  existing validation and behaviour

#### Scenario: Provider requires authentication
- **WHEN** the provider returns neither `user` nor `admin` for a protected operation
- **THEN** the system SHALL return a `not_authorised` authentication-required result
- **AND** it SHALL preserve an opaque handoff when supplied
- **AND** it SHALL not redirect or perform the operation

#### Scenario: User lacks an administrative scope
- **WHEN** a user-scoped caller invokes an admin-protected operation
- **THEN** the system SHALL return a `forbidden` insufficient-authorisation result
- **AND** it SHALL not perform the operation

### Requirement: Direct protected-operation scopes
Each protected tool, resource, or prompt SHALL declare its required `AuthScope`
string-enum value directly. The initial values are `user` and `admin`; `admin`
SHALL satisfy every protected-operation scope. A later change MAY introduce
additional scopes or configurable policy.

Operations without a declared scope SHALL retain existing access behaviour.
The classification SHALL apply only while a provider-backed remote policy is
active and SHALL be enforced after argument validation and before an operation
has an effect. Later protected resources and prompts SHALL use this same
boundary.

#### Scenario: A protected operation is registered
- **WHEN** a tool, resource, or prompt is protected
- **THEN** its registration SHALL identify its required scope enum value
- **AND** that scope requirement SHALL be applied at the request boundary

#### Scenario: An unprotected operation is called with provider active
- **WHEN** a caller invokes an operation without a declared protected scope
- **THEN** the system SHALL preserve that operation's existing access and
  result behaviour

#### Scenario: Export metadata is persisted
- **WHEN** `export_content` or `remove_export` would create or remove persisted
  export metadata while an authentication provider is active
- **THEN** the operation SHALL require the `user` scope
- **AND** it SHALL not change project configuration when authentication is
  required or insufficient
