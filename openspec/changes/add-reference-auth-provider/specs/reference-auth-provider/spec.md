# Spec Delta

## Purpose

Provide a bundled optional OIDC adapter and an independent reference identity
provider that demonstrate and verify Guide's pluggable remote-authentication
contract without making Guide core manage credentials or accounts.

## ADDED Requirements

### Requirement: Optional reference OIDC provider module

The distribution SHALL expose an optional provider named `auth-ref-oidc` through
Guide's authentication-provider entry-point mechanism. Selecting it SHALL
enable the module only when its optional dependencies and provider-owned
configuration are available; it SHALL not enable authentication by default.

The module SHALL validate bearer access tokens issued by a configured OIDC
issuer using the issuer's published verification keys. It SHALL map
provider-owned grants to `AuthScope.USER` and `AuthScope.ADMIN` in a
`UserAuthorisation` result and return only that result and an optional opaque
HTTPS hand-off to Guide. It SHALL not expose raw token content, decoded claims,
credentials, user records, or issuer internals to Guide handlers or templates.

#### Scenario: OIDC module is deliberately selected
- **WHEN** an administrator starts a remote Guide transport with the `auth-ref-oidc` provider selected and valid provider configuration
- **THEN** Guide starts the OIDC module with the remote transport
- **AND** an otherwise unchanged installation without the selection does not load the module

#### Scenario: Valid bearer supplies user access
- **WHEN** a remote caller presents a valid, unexpired bearer access token whose provider-owned grants include `user`
- **THEN** the OIDC module returns `UserAuthorisation` containing `user`
- **AND** Guide does not receive the token or decoded claims beyond the provider contract

#### Scenario: Missing or invalid bearer requires authentication
- **WHEN** a remote caller invokes a protected operation without a valid bearer access token
- **THEN** the OIDC module returns `not_authorised`
- **AND** it may include an opaque HTTPS hand-off to the reference provider

#### Scenario: Valid bearer lacks administrative access
- **WHEN** a remote caller presents a valid bearer access token with `user` but not `admin`
- **THEN** Guide returns `forbidden` for an admin-protected operation
- **AND** it does not return protected operation content or effects

### Requirement: Independent reference OIDC application

The repository SHALL provide an independently runnable reference OIDC identity
provider application as a persistent process. It SHALL own user records,
password verification, signing keys, token issuance, and authentication pages,
and expose standard issuer-discovery and public-key metadata for the bundled
OIDC module.

The selected `auth-ref-oidc` adapter SHALL connect to its configured issuer during startup.
In configured local-reference-provider mode, if the reference provider is
unavailable, the adapter SHALL start it, wait for its discovery endpoint, and
retry. Failure to connect, start, or reach readiness SHALL fail Guide's remote
transport startup. The adapter SHALL stop only a reference-provider process it
started; it SHALL not start or stop an externally managed issuer.

The reference application SHALL offer a browser login/password hand-off that
lets an authenticated user obtain a bearer access token for configuration in a
capable MCP client. It SHALL make clear that the client is responsible for
storing and attaching that bearer on later requests; Guide SHALL not redirect an
MCP request or receive a browser password.

#### Scenario: User completes the hand-off
- **WHEN** a user follows the hand-off URL and successfully completes the reference application's login flow
- **THEN** the application lets that user obtain a bearer access token
- **AND** the token can subsequently be supplied by a capable MCP client to Guide
- **AND** neither the password nor the token is persisted in Guide project or global configuration

#### Scenario: Adapter starts an unavailable local reference provider
- **GIVEN** local-reference-provider mode is configured
- **AND** the configured reference provider is unavailable
- **WHEN** the selected `auth-ref-oidc` adapter starts with a Guide remote transport
- **THEN** it SHALL start the reference-provider process and wait for readiness
- **AND** it SHALL stop that process when the Guide transport stops

#### Scenario: External issuer is unavailable
- **GIVEN** an external issuer is configured
- **AND** the issuer is unavailable
- **WHEN** the selected `auth-ref-oidc` adapter starts with a Guide remote transport
- **THEN** Guide's remote transport startup SHALL fail
- **AND** Guide SHALL NOT attempt to start the external issuer

### Requirement: Encrypted reference user administration and access changes

The reference application SHALL provide an administrator-operated command for
creating, listing, removing, changing the password of, and assigning coarse
`user` or `admin` access to local accounts. It SHALL store only a modern
memory-hard password verifier and SHALL never display or persist a plaintext
password. Password input SHALL use a secure prompt or administrator-controlled
input channel rather than normal command output. Removed accounts SHALL not
receive new tokens; expired tokens SHALL not authorise Guide operations.

The reference provider SHALL persist account data in a SQLCipher-encrypted
SQLite database, accessed through SQLAlchemy and a SQLCipher-capable DBAPI. The
database key SHALL be provider-owned secret configuration and SHALL NOT be
stored in the database, Guide configuration, or command arguments. The
administrator command SHALL call the provider's authenticated management API;
it SHALL NOT open or modify the database directly.

#### Scenario: Administrator grants user access
- **WHEN** an administrator creates an account and assigns `user` access
- **THEN** a subsequently issued valid token permits the named operations mapped
  by the OIDC module to user access
- **AND** it does not permit operations mapped to admin access

#### Scenario: Administrator removes an account
- **WHEN** an administrator removes an account
- **THEN** new authentication and token issuance for that account fail
- **AND** Guide denies later protected requests once the provider's token
  validity and revocation policy requires revalidation

#### Scenario: Administrator command uses the provider API
- **GIVEN** the reference provider is running with its management API available
- **WHEN** an administrator creates or changes an account with the administrator command
- **THEN** the command SHALL authenticate to and use the management API
- **AND** the provider SHALL perform the account mutation
- **AND** the command SHALL NOT directly open the SQLite database

### Requirement: Reference-pair conformance coverage

The OIDC module and reference application SHALL be tested together against a
running reference issuer. The coverage SHALL verify discovery and signing-key
refresh, token expiry, disabled users, permitted and denied operations,
authentication hand-off, and provider lifecycle without using production
credentials.

#### Scenario: Issuer signing key changes
- **WHEN** the reference application rotates its published signing key
- **THEN** the OIDC module refreshes provider-approved verification material
- **AND** it accepts subsequently issued valid tokens and rejects tokens that
  can no longer be verified
