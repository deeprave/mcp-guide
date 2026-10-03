## ADDED Requirements

### Requirement: Dynamic authentication template context
Template rendering with a supplied session SHALL expose an `auth` mapping for
the current request with boolean `active`, `authenticated`, `user`, and `admin`
values. Rendering without a session SHALL omit the mapping.

For a template rendered during a current remote request, `active` SHALL be true
only when a provider is configured for that transport.
Template activity projects the presence of a provider decision for the current
request, including an unauthenticated decision. It is distinct from the
configured-provider check that enables tool enforcement. Session rendering
without a bound provider decision SHALL retain inactive, unrestricted template
predicates without disabling enforcement.
`authenticated`, `user`, and `admin` SHALL express access predicates, not raw
identity claims. When `active` is false, all three scope predicates SHALL be
true. With authentication active, `authenticated` SHALL mean that the caller
has `user` or `admin`; an additional capability scope alone SHALL NOT establish
authenticated state. `admin` true SHALL imply `authenticated` and `user` true. The context
SHALL expose no token, principal, provider configuration, or provider result
detail.

#### Scenario: Authentication is inactive
- **WHEN** a template is rendered with a session without a configured provider or on stdio
- **THEN** `auth.active` SHALL be false
- **AND** `auth.authenticated`, `auth.user`, and `auth.admin` SHALL be true

#### Scenario: Template rendering has no session
- **WHEN** a template is rendered without a supplied session
- **THEN** its context SHALL have no `auth` mapping, even during an authenticated request

#### Scenario: Authenticated non-admin caller renders a template
- **WHEN** a provider-backed caller is authenticated but lacks administrative
  access
- **THEN** `auth.active` and `auth.authenticated` SHALL be true
- **AND** `auth.admin` SHALL be false
- **AND** `auth.user` SHALL be true and `auth.admin` SHALL be false

### Requirement: Request-safe scope projection
The `auth` mapping SHALL be calculated from current request decisions and
SHALL NOT be retained in a session-wide template-context cache. Changes in
caller authentication or provider policy SHALL not cause one caller's
availability values to be rendered for another caller.

#### Scenario: Consecutive callers have different access
- **WHEN** two remote callers with different provider decisions render the same
  template in sequence
- **THEN** each rendering SHALL contain only the current caller's `auth`
  mapping
