## ADDED Requirements

### Requirement: Credential-free provider authorisation context
For a provider-authorised remote request, the application request context SHALL
expose only the transport classification, provider-issued stable principal
identifier, and immutable granted scopes needed for an authorisation decision.
It SHALL not expose raw credentials, bearer tokens, authentication headers,
provider configuration, provider objects, or transport-specific request
objects. Stdio request context SHALL remain trusted for authorisation purposes
without requiring a provider identity.

#### Scenario: Provider authorises an HTTP request
- **WHEN** a selected provider validates a caller before a protected operation
  dispatches
- **THEN** the application request context SHALL expose that caller's principal
  identifier and scopes for the duration of the request
- **AND** it SHALL not expose the provider's request evidence

#### Scenario: Provider is not selected
- **WHEN** a remote request enters the application boundary without a selected
  provider
- **THEN** the request context SHALL not invent a principal or scopes
- **AND** the operation SHALL retain its existing access behaviour

#### Scenario: Stdio request enters the application boundary
- **WHEN** a stdio MCP request enters the application boundary
- **THEN** its request context SHALL permit protected-operation checks to
  recognise the trusted stdio transport
- **AND** it SHALL not construct or require a provider identity
