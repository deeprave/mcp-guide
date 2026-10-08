# Proposal

## Why

The pluggable authentication design needs a real implementation on both sides
of its boundary before its contract can be trusted. A reference OIDC provider
will exercise Guide's provider-module interface against a reference identity
service while supplying a small, understandable local user-management story for
development, testing, and deployments that choose to adopt it.

## What Changes

- Add an optional `auth-ref-oidc` provider module inside the `mcp-guide`
  distribution.
  It is selected through Guide's provider entry-point mechanism and validates
  externally issued OIDC bearer tokens without Guide interpreting credentials
  or managing users.
- Add a reference OIDC provider application in this repository as a persistent
  process. It exposes OIDC discovery, token validation keys, and a
  password-login hand-off. The selected adapter connects to it at transport
  startup and, in configured local-reference mode, starts and owns it when it
  is unavailable.
- Add a user-management command for the reference application to create,
  remove, list, and grant coarse `user` or `admin` access to local accounts,
  with secure password setup and reset. The command uses the provider's
  management API rather than reading or writing its database. The application
  stores password verifiers only, never plaintext passwords.
- Define an end-to-end reference deployment: a user authenticates at the
  identity provider, configures an issued bearer token in a capable MCP client,
  and Guide's OIDC module maps the token to `UserAuthorisation` scopes.
- Use the reference pair as a conformance test for provider lifecycle,
  token validation, key rotation, expired/disabled users, authorisation
  results, and authentication hand-off.

## Capabilities

### New Capabilities

- `reference-auth-provider`: optional Guide OIDC provider integration and an
  independently runnable reference OIDC identity-provider application.

### Modified Capabilities

None.

## Impact

- Adds optional authentication dependencies, provider entry-point metadata,
  an OIDC provider package, a reference identity-provider application, an
  encrypted SQLite user store, and an API-based administration command.
- Depends on the provider contract introduced by `add-mcp-authentication` and
  serves as its executable conformance implementation.
- Adds cryptographic key and password-verifier handling only to the independent
  reference application; Guide's core remains credential- and account-agnostic.
- Is explicitly opt-in and does not alter stdio or remote behaviour when no
  authentication provider is selected.
