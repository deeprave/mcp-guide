## ADDED Requirements

### Requirement: Provider-backed remote ingress
When an authentication provider is selected, a remote MCP transport SHALL start
the provider before accepting protected operations and make its decisions
available to the application authorisation boundary. Direct TLS ingress MAY
pass request authentication evidence to the provider. A transport without a
selected provider SHALL preserve its existing protocol and access behaviour.

#### Scenario: Direct TLS dispatches an authorised request
- **WHEN** a direct-TLS remote transport receives a protected operation
- **THEN** it SHALL pass ephemeral request authentication evidence to the
  selected provider before application dispatch
- **AND** it SHALL dispatch the operation only when the provider authorises it

#### Scenario: Provider is absent
- **WHEN** a remote transport starts without a selected provider
- **THEN** it SHALL preserve existing protocol negotiation and operation access
  behaviour

### Requirement: Trusted-proxy ingress
A Guide HTTP transport behind TLS-terminating infrastructure SHALL use
provider-backed identity assertions only in explicitly configured trusted-proxy
mode. The deployment SHALL ensure that Guide is not directly reachable by
untrusted callers and that the trusted proxy strips caller-supplied identity
headers before forwarding original credentials or an assertion the provider can
verify. The transport SHALL NOT treat `X-Forwarded-Proto`, `X-User`, or similar
headers alone as proof of caller identity.

#### Scenario: Trusted proxy supplies a verifiable assertion
- **WHEN** a trusted-proxy deployment forwards an assertion that the selected
  provider verifies
- **THEN** the provider SHALL make the resulting decision available to the
  protected-operation boundary

#### Scenario: Caller-controlled identity header reaches Guide
- **WHEN** proxy mode receives an identity header that is not verifiable under
  the configured provider policy
- **THEN** the request SHALL be treated as unauthenticated
- **AND** no protected application operation SHALL dispatch

#### Scenario: Public HTTP endpoint claims proxy identity
- **WHEN** a deployment has not explicitly configured trusted-proxy ingress
- **THEN** it SHALL not accept forwarded identity headers as authentication
  evidence
