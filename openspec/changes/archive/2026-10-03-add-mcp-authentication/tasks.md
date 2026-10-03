# Tasks

## 1. Provider contract and direct scopes

- [x] 1.1 Add the single provider-selection CLI option and lazy entry-point loading; verify no provider or optional dependency loads when absent.
- [x] 1.2 Define the provider lifecycle, opaque evidence, request-level authorisation, and hand-off; remove invalidation extensions and verify lifecycle failure cleanup.
- [x] 1.3 Declare direct `AuthScope` values on protected operations; remove the capability registry and verify scope enforcement.

## 2. Enforcement and transport

- [x] 2.1 Start and stop the provider with remote HTTP(S) ingress; deployment owns TLS and proxy policy.
- [x] 2.2 Enforce scope requirements after argument validation and before protected effects; verify Result codes and opaque hand-off, with no raw request evidence exposed to handlers.
- [x] 2.3 Apply the initial policy: user access for project config and conditional SQLite storage; admin access for cloning, permission paths, and global config; unprotected binding, selection, normal callbacks, and `update_documents`.

## 3. Request and template context

- [x] 3.1 Add per-request `auth.active`, `auth.authenticated`, `auth.user`, and `auth.admin` projection; verify inactive auth yields true values and no request data leaks through template caching.
- [x] 3.2 Update onboarding and relevant templates to require authenticated user access before persisting onboarding settings.

## 4. Documentation and verification

- [x] 4.1 Publish ADR-014 and document provider installation, deployment-owned TLS/proxy policy, Result codes, direct-scope policy, hand-off limitation, and no-tenancy boundary.
- [x] 4.2 Add focused unit and remote transport tests, run them in the foreground with formatting/type checks, then run `openspec validate add-mcp-authentication --strict`.

## 5. Review remediation

- [x] 5.1 Replace per-operation provider decisions and `auth.can.*` with request-level `UserAuthorisation` scopes (`user`, `admin`); retain private transport evidence and expose only opaque authorisation state through `RequestContext`.
- [x] 5.2 Apply the scoped access policy: user access for project configuration and document storage; admin access for cloning, permission paths, and global configuration; protect document update and removal.
- [x] 5.3 Use one remote transport lifecycle `finally` path for provider cleanup, preserve session rate limiting when authentication is enabled, and reject provider selection for stdio.
- [x] 5.4 Require user access before persisting onboarding settings; revise deployment documentation so TLS/proxy topology remains administrator responsibility.
- [x] 5.5 Update ADR and delta specifications, including document update/removal and clone scenarios; run formatting, type checks, focused tests, the full suite, and strict OpenSpec validation.

## 6. Incremental review remediation

- [x] 6.1 Permit unauthenticated onboarding inspection and choice collection; require user access before skip or configuration persistence, and align the project-tools specification.
- [x] 6.2 Omit authentication context when no session is supplied; preserve request-specific projection for sessions and verify rendering behaviour.
- [x] 6.3 Centralise the user-or-admin authenticated predicate for denial classification and template projection; align the provider specification and ADR.
- [x] 6.4 Document the rationale for Guide's provider contract rather than framework-level authentication, and align the ADR index terminology.
- [x] 6.5 Reconcile every current review decision, run the full suite and all configured pre-commit checks, and strictly validate the OpenSpec change.

## 7. Result-code alignment

- [x] 7.1 Map missing or invalid authentication to `not_authorised` (HTTP 401 semantics) and insufficient authenticated scope to `forbidden` (HTTP 403 semantics); preserve handoff and MCP transport behaviour, align ADR/specifications/documentation, and verify behavioural tests and strict validation.
