# Spec Delta

## Purpose

Provide repeatable black-box verification that Guide and the independently
operated `auth-guide` service interoperate through their published interfaces.

## ADDED Requirements

### Requirement: Published-boundary compatibility verification
The project SHALL provide an integration suite that starts real Guide and
`auth-guide` processes with disposable state. The suite SHALL use each
service's public configuration, administration, token, HTTPS, and MCP
interfaces, without importing either service's authentication internals.

#### Scenario: Compatibility suite exercises deployed interfaces
- **WHEN** the compatibility suite runs
- **THEN** it SHALL provision test accounts through the provider's public API
- **AND** it SHALL invoke Guide through an MCP client over HTTPS

### Requirement: Authorisation decision compatibility
The suite SHALL verify the outcomes of missing, invalid, ordinary-user, and
administrative bearer evidence against protected Guide operations. It SHALL
verify that a user bearer cannot perform an administrative operation and that
an administrative bearer can satisfy both user and administrative operations.

#### Scenario: Ordinary user invokes an administrative operation
- **GIVEN** an ordinary user token issued by `auth-guide`
- **WHEN** its caller invokes an admin-protected Guide operation
- **THEN** the operation SHALL return `forbidden`
- **AND** it SHALL not perform its protected effect

#### Scenario: Administrative user invokes protected operations
- **GIVEN** an administrative token issued by `auth-guide`
- **WHEN** its caller invokes user- and admin-protected Guide operations
- **THEN** both operations SHALL perform their existing authorised behaviour

### Requirement: Request-level evidence isolation
The suite SHALL verify that Guide evaluates bearer evidence for each request in
one MCP session. A successful higher-privilege request SHALL not authorise a
later request with absent, invalid, or lower-privilege evidence.

#### Scenario: Later request has weaker evidence
- **GIVEN** an MCP session where an admin-protected operation succeeded with an
  administrative bearer
- **WHEN** a later request in that session invokes the operation without a
  bearer or with an ordinary-user bearer
- **THEN** the later request SHALL not perform the administrative effect

### Requirement: Provider availability and trust boundary verification
The suite SHALL verify that an unavailable provider does not prevent
unprotected Guide operations and fails protected operations with the existing
safe `authentication_unavailable` result. It SHALL exercise a service
certificate trusted through the operating-system trust store and verify that an
untrusted certificate fails closed without a Guide-specific trust override.

#### Scenario: Provider becomes unavailable after Guide starts
- **GIVEN** Guide has started with the reference provider selected
- **WHEN** the provider service becomes unavailable
- **THEN** an unprotected operation SHALL retain its existing behaviour
- **AND** a protected operation SHALL return `authentication_unavailable`

#### Scenario: Provider certificate is not trusted
- **GIVEN** the provider uses a certificate absent from the operating-system
  trust store available to Guide
- **WHEN** a protected operation needs an authentication decision
- **THEN** Guide SHALL fail the operation closed
- **AND** the test SHALL not configure a Guide-specific CA override

### Requirement: Supported-platform compatibility execution
The compatibility suite SHALL run in supported Linux and macOS CI
environments. Windows compatibility execution SHALL remain deferred and SHALL
not block the Linux or macOS suite.

#### Scenario: Supported platform job runs
- **WHEN** Linux or macOS compatibility CI is selected
- **THEN** it SHALL run the same published-boundary compatibility scenarios
