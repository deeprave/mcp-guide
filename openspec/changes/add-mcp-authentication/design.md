## Context

Guide's remote transport creates FastMCP's ASGI application, while its public
operation wrappers resolve sessions and enter `RequestContext`. The latter is
the application boundary and must not retain raw ASGI requests or credentials.
Stdio is local and trusted. The existing project hash is a hash of a
client-supplied path and disambiguates local configuration only; it is not a
remote repository or tenancy identity.

## Goals / Non-Goals

**Goals:**

- Load an optional, server-administrator-selected authentication provider for
  remote ingress using CLI configuration.
- Give that provider an asynchronous lifecycle, request authorisation hook,
  optional authentication handoff, and policy/revocation notification channel.
- Keep all credential formats and validation details outside Guide's
  application model.
- Enforce registered scopes centrally at tools, resources, and prompts before
  session creation or an operation's effect.
- Support both direct TLS and explicitly trusted proxy ingress without trusting
  caller-controlled forwarded headers.

**Non-Goals:**

- Guide-managed accounts, passwords, API-token issuance, OAuth discovery, or
  a Guide-hosted login page.
- A built-in credential provider or credential persistence in project/global
  feature-flag configuration.
- Treating FastMCP session IDs, client paths, project hashes, or client
  metadata as caller identity.
- Shared multi-user project hosting, server-generated project identifiers, or
  per-project ACLs.

## Decisions

### 1. CLI-selected provider is the enablement boundary

`--auth-provider <entry-point>` selects a trusted server-side provider module;
omitting it disables provider-backed policy and preserves present transport
behaviour. `--auth-provider-config <reference>` passes an opaque configuration
or secret reference to that module. Guide neither interprets the reference nor
persists its resolved value. A separate global feature flag is unnecessary.

The remote transport constructs and starts the provider when it starts, and
stops it during transport shutdown. Startup fails closed when an enabled
provider cannot initialise. The provider is never constructed for stdio.

### 2. Authenticate lazily at a protected-operation boundary

The operation registry declares a `kind`, name, optional required scope, and
optional validated-argument predicate. After FastMCP validates arguments but
before `request_context_scope`, the boundary looks up the policy. An operation
without a required scope proceeds normally. A protected operation invokes the
provider with ephemeral request authentication evidence and its operation
descriptor.

The provider returns one of:

- authorised, with a stable principal identifier and immutable scopes;
- unauthenticated, optionally with an opaque HTTPS handoff/challenge; or
- forbidden.

Guide maps these to stable MCP-compatible results without disclosing token or
provider details. It must not automatically redirect an MCP invocation to a
browser. A provider that needs interactive authentication owns its HTTPS
callback/login routes and returns a handoff that a capable client can follow
before retrying the operation.

`admin` satisfies `user`; no other hierarchy exists. Initial requirements are
`user` for project administration and conditional SQLite ingestion, and
`admin` for global feature-flag mutation, installed-document updates, and
content export. No existing resource or prompt is initially protected, but the
same registry and boundary apply if one is declared protected later.

### 3. Provider contract and asynchronous notifications

The provider contract has asynchronous `start`, `authorise`, notification, and
`stop` operations. It may keep a connection to an organisation identity or
policy service, receive signing-key rotation or revocation notifications, and
request that Guide invalidate only provider-approved cached decisions.

Guide must obtain a current decision for every protected operation unless the
provider explicitly grants a short-lived cache entry. A notification channel is
therefore an optimisation and revocation aid, not the sole access check.
Provider code is trusted server code; selecting it is deployment-administrator
authority.

### 4. Direct TLS and trusted proxy are explicit ingress modes

For direct TLS, the provider receives the request's authentication evidence
from Guide's HTTPS ASGI boundary. For proxy termination, Guide may run HTTP
behind Nginx only in explicitly configured trusted-proxy mode. Nginx must be
the only reachable upstream, strip all caller-supplied identity headers, and
either forward original credentials or emit an assertion the provider can
verify. `X-Forwarded-Proto`, `X-User`, and similar headers alone are never
proof of identity.

This defines an HTTPS remote boundary even when the Guide process sees HTTP;
it does not authorise a publicly reachable plain HTTP server to trust forwarded
identity headers.

### 5. Scope is not project tenancy

Authentication establishes who calls Guide and a coarse global scope. It does
not prove that a caller owns a client path or may administer a particular
project. The current project hash is `SHA-256(normalised client path)`, so it
can distinguish path strings but cannot identify a repository across hosts or
prevent different clients claiming the same path.

A future shared-hosting design must introduce a server-generated project ID,
server-managed project registration, and principal-to-project roles. Client
paths should remain session-local file coordinates, not persisted authority.

## Risks / Trade-offs

- **Untrusted proxy headers** → require explicit proxy mode, private/mTLS
  upstream reachability, header stripping, and verifiable assertions.
- **Provider outage or bad startup configuration** → fail remote transport
  startup rather than serve an endpoint that appears protected.
- **Provider cache retains revoked access** → provider-controlled short TTLs
  plus revocation notifications; protected operations still ask the provider.
- **Interactive handoff is unsupported by a client** → return an
  MCP-compatible authentication-required result rather than redirecting.
- **Scopes are mistaken for project membership** → document the limitation and
  retain multi-tenant project ACLs as a separate change.

## Migration Plan

1. Release without `--auth-provider`; remote behaviour is unchanged.
2. Deployers select and configure a trusted provider, then start Guide in
   direct-TLS or trusted-proxy mode.
3. Verify an unprotected request, a `user` project mutation, and an `admin`
   server mutation using the provider's own principals.
4. Remove `--auth-provider` and restart to roll back; no Guide credentials,
   accounts, or project migration exist to undo.
