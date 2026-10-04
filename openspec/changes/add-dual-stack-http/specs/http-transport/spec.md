# Spec Delta

## ADDED Requirements

### Requirement: Explicit dual-stack wildcard binding
An HTTP or HTTPS transport URL with the IPv6 wildcard host `[::]` SHALL accept
IPv4 and IPv6 connections on the configured port. If that dual-stack bind is
unsupported or cannot be established, startup SHALL fail with a clear error
rather than silently serve only one address family.

#### Scenario: HTTP wildcard serves both address families
- **GIVEN** the platform supports dual-stack listening
- **WHEN** Guide starts with `http://[::]:8080`
- **THEN** IPv4 and IPv6 clients SHALL reach the same MCP endpoint on port 8080

#### Scenario: HTTPS wildcard serves both address families
- **GIVEN** the platform supports dual-stack listening and valid TLS settings are supplied
- **WHEN** Guide starts with `https://[::]:8443`
- **THEN** IPv4 and IPv6 clients SHALL reach the same TLS-protected MCP endpoint on port 8443

#### Scenario: Requested dual-stack bind cannot be established
- **GIVEN** dual-stack listening is unavailable or the requested bind fails
- **WHEN** Guide starts with an explicit `[::]` endpoint
- **THEN** startup SHALL report a clear failure
- **AND** a bind failure SHALL identify the requested endpoint
- **AND** the CLI SHALL exit non-zero with a concise startup error rather than a traceback
- **AND** Guide SHALL NOT present an IPv4-only or IPv6-only fallback as successful startup

### Requirement: Preserve other bind semantics
Dual-stack wildcard support SHALL NOT change localhost defaults, IPv4 literal
binds, specific IPv6 literal binds or hostname-based address resolution. It
SHALL NOT add a CLI flag, feature flag or authentication requirement.

#### Scenario: Host is omitted
- **WHEN** HTTP or HTTPS is selected without an explicit host
- **THEN** the bind host SHALL remain localhost
- **AND** Guide SHALL NOT listen on non-loopback interfaces

#### Scenario: Explicit IPv4 wildcard
- **WHEN** the endpoint host is `0.0.0.0`
- **THEN** the transport SHALL retain its IPv4-only all-interface bind

#### Scenario: Specific IPv6 address
- **WHEN** the endpoint host is a specific IPv6 address such as `[::1]`
- **THEN** the transport SHALL bind that address without broadening it to a wildcard

#### Scenario: Hostname resolves to both address families
- **GIVEN** a hostname resolves to usable local IPv4 and IPv6 bind addresses
- **WHEN** that hostname is selected as the endpoint host
- **THEN** the transport SHALL preserve binding to those resolved addresses
- **AND** it SHALL NOT replace the hostname with an all-interface wildcard

### Requirement: Shared application and listener lifecycle
Both address families SHALL use the same MCP application, endpoint path, TLS
configuration, optional authentication and request-admission policy. Every
listener created for the transport SHALL be released on shutdown or failed
startup, including cancellation during startup.

#### Scenario: Protected operation has address-family parity
- **GIVEN** a provider is configured and a caller lacks access to a protected operation
- **WHEN** that caller invokes the operation over IPv4 or IPv6
- **THEN** Guide SHALL apply the same authorisation requirement and denial behaviour

#### Scenario: Authentication remains optional
- **GIVEN** no authentication provider is configured
- **WHEN** Guide serves a dual-stack endpoint
- **THEN** existing operation access behaviour SHALL remain unchanged for both families

#### Scenario: Transport relinquishes its listener
- **GIVEN** the transport has created a listener
- **WHEN** the transport stops or startup fails or is cancelled
- **THEN** the listener SHALL be closed and its bind released
