## ADDED Requirements

### Requirement: Credential-free authorisation context
For a provider-backed remote request, the application request context SHALL
retain only the opaque `UserAuthorisation` state for the current request. It
SHALL NOT expose raw credentials, bearer tokens, authentication headers,
provider configuration, provider objects, principals, or transport-specific
request objects. The scope names are limited to Guide's access boundary and do
not expose provider claims.
Stdio request context SHALL remain trusted for authorisation purposes without
requiring provider identity.

#### Scenario: Provider authorises an HTTP request
- **WHEN** a selected provider validates a caller before a protected operation
  dispatches
- **THEN** the request context SHALL retain only `UserAuthorisation` needed for
  the request
- **AND** it SHALL not expose the provider's request evidence or claims

#### Scenario: Provider is not selected
- **WHEN** a remote request enters the application boundary without a selected
  provider
- **THEN** the request context SHALL provide no provider authorisation state
- **AND** the operation SHALL retain its existing access behaviour

#### Scenario: Stdio request enters the application boundary
- **WHEN** a stdio MCP request enters the application boundary
- **THEN** its request context SHALL recognise the trusted stdio transport
- **AND** it SHALL not construct or require a provider identity
