# Design

## Context

`add-mcp-authentication` establishes Guide's generic remote-provider boundary.
The reference provider service is now developed and operated outside this
repository. This change implements only the Guide-side adapter that consumes
that service; it does not implement or own any provider-service behaviour.

## Goals / Non-Goals

**Goals:**

- Connect a selected Guide provider module to the external reference provider
  service using the service's TLS authentication interface.
- Turn a validated, minimal service decision into the request-local
  `UserAuthorisation` result required by Guide's protected-operation boundary.
- Make the service interface, failure behaviour, trust configuration, and
  ownership boundary explicit and testable.

**Non-Goals:**

- Implement, start, stop, supervise, or configure the reference provider
  process.
- Implement accounts, passwords, persistent tokens, signing keys, login pages,
  hand-off pages, or provider administration.
- Add a Guide CLI option for provider-specific configuration or a Guide-managed
  credential store.
- Pass account identifiers, raw tokens, decoded claims, or provider objects to
  Guide handlers or templates.

## Decisions

### External service is the sole identity and lifecycle owner

The adapter is selected through Guide's existing authentication-provider
entry-point mechanism. Its configuration identifies a pre-existing, TLS-secured
reference provider service through the provider-owned `AG_ADDRESS` environment
variable. The adapter builds a `truststore` system-trust context; an operator
installs any private provider authority in the operating-system or container
trust store rather than passing a CA bundle to Guide. Guide only receives the
selected entry-point name and does not add a provider-config CLI argument.

Guide never starts, stops, waits for, or otherwise supervises the service. The
service operator is responsible for availability, account bootstrap,
credentials, login/token provisioning, rotation, and administration. Provider
startup does not contact the service, so provider unavailability does not stop
the configured remote Guide transport from serving operations that do not need
an authentication decision.

### Adapter uses the narrow Guide authentication endpoint

For each protected remote operation, the adapter sends that request's bearer
evidence to the service's versioned Guide authentication endpoint over TLS. A
successful response is an authentication decision, not a provider session or
identity object. The adapter accepts only the response fields defined for Guide
access: an optional list of recognised Guide scopes. It discards any account
identifier or other service metadata before returning to Guide.

A successful decision grants `AuthScope.USER`. If the service decision includes
the recognised `admin` scope, the adapter also grants `AuthScope.ADMIN`; Guide's
existing rule makes admin satisfy user access. Unknown, duplicated, malformed,
or contradictory scopes fail closed. Missing, invalid, or rejected bearer
evidence produces an unauthenticated `UserAuthorisation`, allowing Guide to
return its existing `not_authorised` result. The adapter neither parses a token
format nor retains bearer evidence beyond the request.

The current reference service interface is `POST /v1/authenticate` with bearer
request authentication and a JSON decision containing `scopes`; this is the
only service route in scope. Guide must use the service's normal TLS trust
configuration and must not disable certificate verification.

### Provider result and transport failures fail closed

The adapter treats invalid responses, unexpected content types, TLS failures,
connection errors, timeouts, and service errors as provider failures. It emits only safe
operational diagnostics and does not log bearer values or response bodies. The
remote request fails closed through the existing provider-failure path; Guide
must not substitute a cached authorisation decision or silently allow an
operation.

### Confirmed entrypoint and service contract

The public adapter entry-point name is `auth-ref`. It identifies the reference
provider integration and uses the provider service's direct bearer-validation
endpoint.

The configured service base endpoint supplies `POST /v1/authenticate`. The
adapter forwards only the incoming `Authorization: Bearer <token>` request
evidence. A successful `200` JSON response contains a `scopes` list and may
include provider-private account identity, which the adapter discards. An empty
scope list grants Guide `user`; the only recognised service scope is `admin`,
which additionally grants Guide `admin`. Missing or invalid bearer evidence
receives `401` and maps to unauthenticated access. Any other response status,
malformed success response, TLS failure, or connection failure is a provider
failure and fails closed.

The adapter allows five seconds for each provider connection or authentication
decision. A connection timeout, TLS failure, or other connection failure reports
that Guide could not connect to the authentication service. A timeout after the
connection phase reports that the authentication service did not respond in
time. These safe diagnostics do not expose bearer evidence or provider response
content.

The HTTP authentication middleware retains only ephemeral evidence. A protected
operation obtains and checks its decision at its own authorisation boundary.
It returns the corresponding safe `authentication_unavailable` Result when the
provider cannot connect or answer, while unprotected operations do not contact
the provider. This lets the caller distinguish a provider connectivity problem
from an unanswered authentication decision without making provider availability
a dependency of basic Guide operations.

When request evidence is bound but no decision is required or available,
template `auth` predicates are active and fail closed: `authenticated`, `user`,
and `admin` are all false. This prevents unprotected remote rendering from
revealing content guarded by administrative predicates without making rendering
contact the provider.

The adapter does not probe the service at startup. It contacts the endpoint
only while obtaining a request's current authentication decision. This preserves
Guide availability for operations that do not need authentication while still
failing closed whenever a protected operation cannot obtain its decision.

### Templates gate scope predicates on active enforcement

Template scope predicates describe the current request; they do not alone mean
that the transport is enforcing authentication. `auth.active` is the sole outer
authentication gate: a conditional on `auth.authenticated`, `auth.user`, or
`auth.admin` must occur only within its corresponding `auth.active` section.
When authentication is inactive, including stdio, the template must retain the
existing action rather than presenting a credential hand-off. This keeps
authentication-aware guidance from becoming a blocker for trusted local
operation.

## Risks / Trade-offs

- [Provider service is unavailable] → fail only requests that need an
  authentication decision safely; availability and recovery remain the provider
  operator's concern.
- [Provider service stalls] → time out after five seconds and fail closed with
  a diagnostic that distinguishes an unavailable service from an unanswered
  authentication decision.
- [A service response grows provider-private fields] → accept only the narrow
  recognised scope decision and discard everything else.
- [Service and adapter contract drift] → version the endpoint contract,
  maintain integration tests against a fake TLS service, and reject malformed
  responses.
- [Bearer data leaks through diagnostics] → never log request authorisation
  headers, bearer values, or response bodies.

## Migration Plan

1. Install the adapter's optional dependency and the independently distributed
   reference provider service.
2. Configure and start the provider service under its own operational model.
3. Select the adapter for a remote Guide transport and configure its
   provider-owned TLS endpoint/trust settings.
4. Roll back by removing the provider selection. No Guide account, token, or
   provider-service state requires migration.
