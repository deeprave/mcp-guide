# Tasks

## 1. Confirm the service-adapter contract

- [x] 1.1 Reconcile `add-mcp-authentication` with the final Guide provider contract: one provider-selection option; request-level `UserAuthorisation` with `user`/`admin` `AuthScope` values; `not_authorised` for missing or invalid authentication; `forbidden` for insufficient authenticated scope; `admin` satisfying `user`; no raw token, claim, or principal in Guide handlers; and no export-state capability. Verify strict OpenSpec validation passes for the reference change and canonical specifications.
- [x] 1.2 Confirm the public adapter entry-point name and the external provider service's versioned Guide authentication contract before implementation. Record the TLS endpoint, accepted bearer-evidence transport, recognised response scope values, invalid-token response, and service-failure semantics without expanding Guide's provider interface.

## 2. Implement the optional Guide service adapter

- [x] 2.1 Add the optional provider entry point and HTTP client dependency, with provider-owned endpoint and TLS-trust configuration and lazy loading. Verify a normal installation and a server without provider selection do not import the adapter dependency.
- [x] 2.2 Implement adapter lifecycle and per-request service calls: connect only to the configured external service, forward request bearer evidence only over verified TLS, validate the narrow response, and return request-local `UserAuthorisation` scopes. Verify Guide never receives a principal, account identifier, raw token, decoded claim, or provider object.
- [x] 2.3 Map successful external decisions to `user` and optional `admin`; map rejected bearer evidence to unauthenticated access; fail closed for malformed responses, unknown scopes, TLS errors, connection errors, and service failures. Verify diagnostics contain no bearer values or provider response bodies.

## 3. Verify and document the boundary

- [x] 3.1 Add adapter tests using a disposable TLS provider-service double. Verify valid user/admin decisions, absent/invalid bearer evidence, malformed and unknown scopes, service rejection, connection failure, certificate-validation failure, and fresh authorisation on every request.
- [x] 3.2 Document optional installation, remote transport selection, provider-owned endpoint/trust configuration, service lifecycle ownership, and bearer provisioning. State that the external provider—not Guide—owns accounts, credentials, tokens, login, administration, and availability.
- [x] 3.3 Run `openspec validate add-reference-auth-provider --strict`, the targeted adapter tests in the foreground, and applicable formatting and type checks; verify all commands pass.

## 4. Correct provider naming and bounded failure behaviour

- [x] 4.1 Rename the adapter module, public entry point, optional dependency, tests, and operator documentation from the obsolete OIDC-specific name to `auth-ref`.
- [x] 4.2 Bound provider connection and authentication-decision requests to five seconds, distinguish safe connection and timeout diagnostics, and preserve fail-closed behaviour without bearer leakage.
- [x] 4.3 Add behavioural coverage for a timed-out authentication decision and rerun the targeted adapter checks.
- [x] 4.4 Preserve safe connection-versus-timeout classification through the provider-neutral protected-operation boundary, returning the corresponding `authentication_unavailable` Result without dispatching the protected effect.
- [x] 4.5 Remove the external-service readiness probe from provider startup so an unavailable provider does not stop remote Guide from serving operations that do not need authentication.
- [x] 4.6 Bind request evidence at HTTP ingress and obtain provider decisions only at protected tool boundaries; return safe `authentication_unavailable` Results for provider failures without blocking unprotected operations.
- [x] 4.7 Audit every bundled template: any conditional on `auth.authenticated`, `auth.user`, or `auth.admin` is nested within `auth.active`; inactive authentication retains the original action. Verify stdio onboarding and manual-skip guidance do not ask for authentication, then rerun the focused template-context tests.
