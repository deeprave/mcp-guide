## ADDED Requirements

### Requirement: Localhost transport defaults
Bare HTTP and HTTPS modes, and transport URLs without a host, SHALL bind to
localhost. Listening on another interface, including all interfaces, SHALL
require an explicit host in the transport URL. This bind default SHALL NOT
introduce a requirement to configure authentication for remote access.

#### Scenario: HTTPS has no explicit host
- **WHEN** HTTPS is selected without an explicit host
- **THEN** Guide SHALL bind to localhost

#### Scenario: All-interface endpoint is explicit
- **WHEN** the transport URL specifies `0.0.0.0` as its host
- **THEN** Guide SHALL retain that explicitly requested bind address
- **AND** provider selection SHALL remain optional

### Requirement: Provider-backed remote ingress
When an authentication provider is selected with `--auth-provider`, a remote
MCP transport SHALL start the provider before accepting protected operations
and make its opaque request authorisation available to the application
boundary. Direct HTTPS ingress MAY pass ephemeral request authentication
evidence to the provider. A transport without a selected provider SHALL
preserve its existing protocol and access behaviour.

#### Scenario: HTTP(S) dispatches an authorised request
- **WHEN** a remote HTTP or HTTPS transport receives a protected operation
- **THEN** it SHALL pass ephemeral request authentication evidence to the
  selected provider before application dispatch
- **AND** it SHALL dispatch the operation only when the resulting request
  scopes satisfy that operation's requirement

#### Scenario: Provider is absent
- **WHEN** a remote transport starts without a selected provider
- **THEN** it SHALL preserve existing protocol negotiation and operation access
  behaviour

### Requirement: Deployment-owned transport security
Guide SHALL activate a selected provider for either HTTP or HTTPS and SHALL
not enforce TLS, reverse-proxy, or header-trust policy itself. Direct HTTPS or
HTTP behind TLS-terminating infrastructure are recommended deployment designs.
The deployment administrator and the configured provider SHALL determine which
request evidence is acceptable.

#### Scenario: TLS terminates at a reverse proxy
- **WHEN** a provider is selected for a Guide HTTP upstream behind a
  TLS-terminating reverse proxy
- **THEN** Guide SHALL activate the provider and pass the request evidence it
  receives to that provider
- **AND** it SHALL not impose additional TLS or proxy policy
