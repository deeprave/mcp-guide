## MODIFIED Requirements

### Requirement: Dynamic authentication template context
Template rendering with a supplied session SHALL expose an `auth` mapping for
the current request with boolean `active`, `authenticated`, `user`, and `admin`
values. Rendering without a session SHALL omit the mapping.

For a template rendered during a current remote request, `active` SHALL be true
when provider-backed request evidence is bound for that transport. Template
activity projects the presence of a provider decision for the current request,
including an unauthenticated decision. It is distinct from the configured-provider
check that enables tool enforcement. Session rendering with provider-backed
request evidence but without a bound provider decision SHALL retain active,
fail-closed predicates: `authenticated`, `user`, and `admin` SHALL be false.
This projection SHALL NOT require a provider call.
`authenticated`, `user`, and `admin` SHALL express access predicates, not raw
identity claims. When `active` is false, all three scope predicates SHALL be
true. With authentication active, `authenticated` SHALL mean that the caller
has `user` or `admin`; an additional capability scope alone SHALL NOT establish
authenticated state. `admin` true SHALL imply `authenticated` and `user` true.
Template conditionals SHALL use `auth.active` as the sole outer authentication
gate. A conditional on `auth.authenticated`, `auth.user`, or `auth.admin` SHALL
occur only within a corresponding `auth.active` section. An inactive
authentication boundary SHALL retain the action's existing instructions
regardless of a scope predicate.
The context SHALL expose no token, principal, provider configuration, or
provider result detail.

#### Scenario: Authentication is inactive
- **GIVEN** a session is supplied without a configured provider or on stdio
- **WHEN** a template is rendered with a session without a configured provider or on stdio
- **THEN** `auth.active` SHALL be false
- **AND** `auth.authenticated`, `auth.user`, and `auth.admin` SHALL be true

#### Scenario: Inactive authentication does not prompt for credentials
- **GIVEN** a session is supplied without a configured provider or on stdio
- **WHEN** an authentication-aware template renders an otherwise available
  configuration action
- **THEN** it SHALL present the action without instructing the caller to
  authenticate

#### Scenario: Remote rendering has no provider decision
- **GIVEN** provider-backed remote request evidence is bound
- **AND** no provider decision is bound for the current request
- **WHEN** a template is rendered with a session
- **THEN** `auth.active` SHALL be true
- **AND** `auth.authenticated`, `auth.user`, and `auth.admin` SHALL be false

#### Scenario: Template rendering has no session
- **GIVEN** no session is supplied
- **WHEN** a template is rendered without a supplied session
- **THEN** its context SHALL have no `auth` mapping, even during an authenticated request

#### Scenario: Authenticated non-admin caller renders a template
- **GIVEN** the provider-backed caller is authenticated but lacks administrative access
- **WHEN** a provider-backed caller is authenticated but lacks administrative
  access
- **THEN** `auth.active` and `auth.authenticated` SHALL be true
- **AND** `auth.admin` SHALL be false
- **AND** `auth.user` SHALL be true and `auth.admin` SHALL be false
