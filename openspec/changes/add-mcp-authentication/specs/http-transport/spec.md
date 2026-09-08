## ADDED Requirements

### Requirement: Authenticated HTTP(S) request dispatch
When optional MCP authentication is configured, the HTTP and HTTPS transport
SHALL validate caller credentials and make the resulting identity and scopes
available to application authorisation before a protected operation executes.
The transport SHALL preserve existing protocol negotiation and response
semantics for authorised and unprotected requests.

#### Scenario: Authenticated request reaches a protected operation
- **WHEN** a caller supplies valid credentials for an HTTP or HTTPS MCP request
- **THEN** the transport SHALL make the caller's identity and scopes available
  for the operation's authorisation decision
- **AND** it SHALL dispatch the operation only if that decision succeeds

#### Scenario: Protected operation lacks valid authentication
- **WHEN** a protected HTTP or HTTPS MCP operation has no valid caller identity
- **THEN** the transport SHALL return the applicable authentication or
  authorisation result
- **AND** it SHALL not dispatch the operation's application handler

#### Scenario: Unprotected request has no credentials
- **WHEN** an unauthenticated caller invokes an unprotected HTTP or HTTPS MCP
  operation
- **THEN** the transport SHALL preserve the operation's existing protocol and
  application behaviour
