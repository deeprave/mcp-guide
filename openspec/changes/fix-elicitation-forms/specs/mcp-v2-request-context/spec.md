# Spec Delta

## MODIFIED Requirements

### Requirement: Client-aware inherited-PWD bootstrap
Inherited-PWD bootstrap SHALL require explicit opt-in and shared stdio state. Shared
state SHALL be established either by the filesystem probe or, at startup, by the
opted-in stdio evidence described below. It SHALL NOT use server PWD while sharing
is unverified, failed or disabled.

#### Scenario: Unverified or HTTP inherited PWD
- **WHEN** bootstrap is enabled but shared stdio access is not verified
- **THEN** the interaction SHALL remain unbound until given an absolute client root

#### Scenario: Verified inherited PWD
- **WHEN** stdio sharing is verified and inherited-PWD bootstrap is explicitly enabled
- **THEN** bootstrap MAY bind through LazyPath.client_resolve()

#### Scenario: Opted-in stdio with PWD as the server directory
- **WHEN** the process uses the stdio transport and inherited-PWD bootstrap is explicitly enabled
- **AND** `PWD` is set, absolute, and an existing directory
- **AND** that directory is the same directory as the server's working directory
- **THEN** the server SHALL treat client filesystem sharing as verified at startup
- **AND** SHALL NOT run the filesystem probe
- **AND** the first unbound interaction, on a legacy or `2026-07-28` connection, MAY bind from `PWD` without `set_project`
- **AND** a request that supplies a `session_id` SHALL NOT infer a root from `PWD`

#### Scenario: Evidence is missing or does not match
- **WHEN** inherited-PWD bootstrap is enabled but `PWD` is unset, relative, not a directory,
  or a different directory from the server's working directory
- **THEN** the server SHALL NOT treat client filesystem sharing as verified
- **AND** the interaction SHALL be bound with `set_project` and the probe SHALL apply

#### Scenario: Remote transports
- **WHEN** the transport is HTTP or HTTPS
- **THEN** the opt-in SHALL NOT establish shared state
