# ADR-014: Pluggable Remote Authentication Provider

**Status:** Accepted
**Date:** 2026-10-01
**Related changes:** `add-mcp-authentication`, `add-reference-auth-provider`

## Context

Guide's stdio transport is a local, trusted integration. A remotely reachable
HTTP(S) transport has a different boundary: it may be used directly over HTTPS
or be reached through a TLS-terminating reverse proxy. Project checksums and
client paths distinguish local project configuration; they do not identify a
remote caller or establish tenancy.

Guide needs optional protection for selected operations without acquiring user
accounts, passwords, token formats, identity-claim semantics, or a built-in
authentication service. The authentication system must also support an
operator's existing identity service and permit a reference provider to live
outside Guide's normal server lifecycle.

## Decision

### Provider discovery and lifecycle

An operator enables remote authentication by selecting one Python provider
entry point:

```text
--auth-provider <provider-name>
```

`<provider-name>` is resolved from the `mcp_guide.auth_providers` entry-point
group. Guide dynamically loads the selected factory only when a remote HTTP(S)
transport is started. It constructs, starts, and stops that provider with that
transport. Stdio never loads, creates, or calls a provider. Provider-specific
configuration belongs to the provider's deployment environment, such as its
own environment variables, configuration file, or external service; Guide has
no provider-configuration CLI option.

A selected provider that cannot be loaded or started prevents its remote
transport from serving. No provider selected means current remote behaviour is
preserved.

### Python provider contract

The dynamically loaded factory returns an asynchronous `AuthProvider` module
implementation. The exact Python types will live in Guide's public auth module;
the contract has these responsibilities:

- `start()` and `stop()` initialise and release provider-owned resources.
- `authenticate(evidence)` accepts only ephemeral request evidence and returns
  `UserAuthorisation` for that request.

`UserAuthorisation` contains scope names and an optional opaque HTTPS
authentication handoff. The handoff is a provider-owned URL or challenge that a
capable client may use before retrying the MCP request. Guide does not redirect
MCP requests, host login pages, receive passwords, issue tokens, or interpret
the handoff.

The evidence is deliberately opaque to Guide's application handlers. A
provider can validate a bearer token, validate a reverse-proxy assertion, or
use another credential mechanism. It may inspect its own claims, principals,
roles, and scopes internally, but it returns only Guide access scopes and an
optional handoff. Guide does not expose credentials, provider claims, or raw
request evidence to tools, prompts, resources, templates, logs, or persisted
session state.

### Transport boundary

Either HTTP or HTTPS passes request evidence to the selected provider. Guide
does not enforce TLS, reverse-proxy, or header-trust policy: that is entirely a
deployment responsibility. Direct HTTPS, or HTTP behind TLS-terminating
infrastructure, are the recommended remote deployments.

HTTP and HTTPS default to localhost, including URLs without a host. Binding to
another interface requires an explicit host in the transport URL. This safer
bind default does not make authentication mandatory or introduce deployment
policy checks.

Guide's middleware uses the synchronous `bind_user_authorisation()` context
manager to bind the provider decision while handling a request and restore the
previous state on every exit. `current_user_authorisation()` exposes that
decision to RequestContext construction and template projection. These are
Guide integration helpers, not additional provider-interface methods.

### Why Guide owns the operation boundary

FastMCP and the MCP SDK provide transport authentication and OAuth integration
facilities. Applying their authentication requirement to the whole HTTP endpoint
would also block Guide's deliberately unprotected operations, such as project
binding, configuration inspection, and ordinary file callbacks. Guide instead
checks the required scope at each protected operation and preserves trusted stdio
behaviour on the same server implementation.

The provider contract also permits authentication systems beyond OAuth without
making Guide own login routes, token formats, or identity claims. A provider may
use FastMCP or MCP SDK facilities internally; it still returns Guide's
`UserAuthorisation` through the same contract.

### Direct scope enforcement and access modes

A protected tool, resource, or prompt declares its required `AuthScope` enum
value directly. Guide evaluates it against the request's `UserAuthorisation`
after validation but before any protected effect. The initial scope enum values
are `user` and `admin`; `admin` is the unrestricted override and satisfies all
other scope checks. A future change may introduce additional scopes or a
configurable capability policy when that is needed.

The effective modes are:

| Mode | Meaning | Result for protected operation |
| --- | --- | --- |
| Authentication inactive | No provider is selected. | All protected operations are available; existing behaviour applies. |
| Unauthenticated | A provider is active but returns neither `user` nor `admin`. | Guide returns its authentication-required Result and may include the opaque handoff. |
| User access | `UserAuthorisation` contains `user`. | Guide performs user-protected operations. |
| Administrator access | `UserAuthorisation` contains `admin`, which Guide treats as also having `user`. | Guide performs user and admin-protected operations. |

“User” and “administrator” are Guide access scopes, not identities. A provider
may map its own roles or claims to them in any way it chooses. Guide produces
`not_authorised` for missing or invalid authentication (HTTP 401 semantics), and
`forbidden` for an authenticated caller without the required scope (HTTP 403
semantics). The authentication-required response may include the opaque handoff.
These are Guide Result codes inside MCP responses; they do not change HTTP
transport statuses or introduce `WWW-Authenticate` challenges.
Authenticated state means `user` or `admin`, and unauthenticated state is its
complement. Any future capability scope must accompany `user` unless `admin`
is present; a capability scope alone does not establish authentication.

Templates receive only request-specific boolean availability:

```yaml
auth:
  active: true
  authenticated: false
  user: false
  admin: false
```

When authentication is inactive, `auth.active` is false; `authenticated`,
`user`, and `admin` are true. `auth.admin` implies `auth.authenticated` and
`auth.user`. This projection is recalculated per request and is never stored in
a shared template-context cache.

Transport scope enforcement and template activity describe different contexts.
`scope_enforcement_enabled` tests whether the runtime has a configured provider;
protected tools fail closed when enforcement is enabled but no request decision
is available. Template projection uses `request_has_provider_decision` to express
whether a provider decision is bound to the current request, including an
anonymous decision. Without a bound decision, session rendering retains its
inactive, unrestricted defaults; this does not disable tool enforcement.
Rendering without a supplied session omits the `auth` mapping entirely.

Onboarding may inspect existing configuration and collect or confirm choices
without authentication. Saving those choices, including marking onboarding as
skipped, requires user access while authentication is active.

The initial policy leaves `set_project`, `switch_project`, ordinary file
callbacks, and `update_documents` available. It requires user access for
project configuration and SQLite document ingestion, and admin access for
cloning, project permission paths, and global configuration. While export
operations persist project export metadata and write permissions, creating or
removing that state requires user access. `retire-export-metadata` will make
export a stateless client-side handoff and can remove that temporary protection.

## Consequences

- Guide has a stable, testable authorisation boundary without becoming an
  identity provider.
- Operators can integrate an existing provider, or install the separately
  runnable reference OIDC provider, without changing Guide credentials or
  deployment configuration.
- A provider package has a narrow public compatibility surface: its factory,
  lifecycle, request authorisation method, and optional handoff.
- Tool, prompt, and resource policy can grow without leaking provider-specific
  identity semantics into Guide. Any future configurable policy must still use
  named scopes and direct operation declarations.
