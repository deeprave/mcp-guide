# Spec Delta

## Purpose

Provide a bundled optional OIDC adapter and an independent reference identity
provider that demonstrate and verify Guide's pluggable remote-authentication
contract without making Guide core manage credentials or accounts.

## ADDED Requirements

### Requirement: Optional OIDC provider module

The distribution SHALL expose an optional provider named `oidc` through
Guide's authentication-provider entry-point mechanism. Selecting it SHALL
enable the module only when its optional dependencies and provider-owned
configuration are available; it SHALL not enable authentication by default.

The module SHALL validate bearer access tokens issued by a configured OIDC
issuer using the issuer's published verification keys. It SHALL map the
provider's claims to named Guide operation decisions and return only the
provider-contract decision, optional hand-off, and bounded availability results
to Guide. It SHALL not expose raw token content, claims, credentials, user
records, or issuer internals to Guide handlers or templates.

#### Scenario: OIDC module is deliberately selected
- **WHEN** an administrator starts a remote Guide transport with the `oidc` provider selected and valid provider configuration
- **THEN** Guide starts the OIDC module with the remote transport
- **AND** an otherwise unchanged installation without the selection does not load the module

#### Scenario: Valid bearer permits an operation
- **WHEN** a remote caller presents a valid, unexpired bearer access token whose provider-owned access grants permit a named operation
- **THEN** the OIDC module returns `allow` for that operation
- **AND** Guide does not receive the token or decoded claims beyond the provider contract

#### Scenario: Missing or invalid bearer requires authentication
- **WHEN** a remote caller invokes a protected operation without a valid bearer access token
- **THEN** the OIDC module returns `not_authorised`
- **AND** it may include an opaque HTTPS hand-off to the reference provider

#### Scenario: Valid bearer lacks access
- **WHEN** a remote caller presents a valid bearer access token that does not permit a named operation
- **THEN** the OIDC module returns `forbidden`
- **AND** it does not return protected operation content or effects

### Requirement: Independent reference OIDC application

The repository SHALL provide an independently runnable reference OIDC identity
provider application. It SHALL be deployed and started separately from Guide,
own user records, password verification, signing keys, token issuance, and
authentication pages, and expose standard issuer-discovery and public-key
metadata for the bundled OIDC module.

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

#### Scenario: Guide transport is unavailable
- **WHEN** the Guide transport is stopped
- **THEN** the independently started reference identity-provider application remains independently manageable

### Requirement: Reference user administration and access changes

The reference application SHALL provide an administrator-operated command for
creating, listing, disabling, changing the password of, and assigning coarse
`user` or `admin` access to local accounts. It SHALL store only a modern
memory-hard password verifier and SHALL never display or persist a plaintext
password. Disabled accounts and expired tokens SHALL not authorise Guide
operations.

#### Scenario: Administrator grants user access
- **WHEN** an administrator creates an account and assigns `user` access
- **THEN** a subsequently issued valid token permits the named operations mapped
  by the OIDC module to user access
- **AND** it does not permit operations mapped to admin access

#### Scenario: Administrator disables an account
- **WHEN** an administrator disables an account
- **THEN** new authentication and token issuance for that account fail
- **AND** Guide denies later protected requests once the provider's token
  validity and revocation policy requires revalidation

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
