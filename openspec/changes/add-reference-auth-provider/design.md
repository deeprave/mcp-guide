# Design

## Context

`add-mcp-authentication` establishes a generic remote provider boundary but
does not prove that an external identity system can satisfy it. This change
adds a reference pair in the same distribution: an optional Guide-side OIDC
module and an independent identity-provider application. See the proposal and
the `reference-auth-provider` requirements for the behaviour contract.

## Goals / Non-Goals

**Goals:**

- Exercise the Guide provider lifecycle, named-operation decisions, hand-off,
  cache invalidation, and template availability boundary against a real issuer.
- Keep the two runtime processes independently deployable, startable, and
  failure-isolated.
- Give adopters a compact example of account administration and token issuance
  without changing Guide core into an account service.

**Non-Goals:**

- A general-purpose, high-scale, or managed identity product.
- A Guide-managed login page, password database, signing key, or token store.
- Automatic browser redirects or automatic bearer-token installation in an MCP
  client.
- Per-project roles or tenancy; access remains provider-global and coarse.

## Decisions

### Two packages, one distribution, two processes

Place the Guide adapter under the main package as an optional OIDC provider
entry point. Place the reference identity-provider application in a distinct
namespaced package with its own executable command. Both ship in the
distribution, but the Guide server starts only the selected adapter; the
identity-provider application is always a separately managed process.

This preserves one repository and compatible releases, much like the existing
script entry points, while retaining the operational boundary. An independent
repository or distribution remains possible later if the reference application
outgrows this release cadence.

### OIDC module is a resource-server adapter

The `oidc` module discovers issuer metadata and public signing keys, validates
bearer access tokens, and maps provider-owned grants to Guide's registered
named operations. Guide receives only contract decisions and boolean
availability for its bounded capability map. It receives neither raw scopes nor
a principal identity as an application-level authorisation input.

Provider configuration belongs to the module's deployment environment, not an
additional Guide CLI argument or persisted Guide configuration. This preserves
the single provider-selection option and lets credentials remain under the
identity-provider operator's control.

### Simple local accounts, standards-based tokens

The reference application keeps a local user store with Argon2id password
verifiers, coarse user/admin grants, asymmetric signing keys, short-lived
access tokens, OIDC discovery metadata, and JWKS key publication. Its admin
command is the bootstrap and management surface; credentials are accepted only
through its HTTPS login flow or administrator-controlled command input.

Use a mature standards and cryptography implementation rather than composing
password hashing, JWT handling, or protocol cryptography directly. The exact
library is an implementation dependency selected during the implementation
task.

### Handoff provisions client authentication; it does not redirect MCP

For an unauthenticated protected operation, the OIDC module returns the
reference application's opaque HTTPS login/token-provisioning URL. After login,
the user configures the issued bearer in their MCP client and retries. This
works with clients that cannot host an OAuth callback and keeps browser/session
cookies out of Guide.

An alternative authorisation-code callback flow would be more automated but
requires every MCP client to implement a callback receiver and secure token
storage. It is intentionally outside this first reference application.

## Risks / Trade-offs

- [A reference application is mistaken for a complete production IdP] → label
  its operational limits prominently and recommend an organisation's existing
  OIDC issuer where appropriate.
- [A local password flow is attacked] → use modern password verifiers, HTTPS,
  rate limiting, generic login failures, short-lived tokens, and no password or
  token logging.
- [Key rotation leaves cached decisions valid] → honour provider-controlled
  expiry/invalidation and test JWKS refresh and token rejection.
- [Clients cannot attach a configured bearer] → hand-off remains informative;
  automatic client credential installation is explicitly out of scope.

## Migration Plan

1. Release the optional OIDC dependencies and provider entry point without
   changing default Guide behaviour.
2. Start the reference identity-provider application, create an administrator
   and users through its management command, then configure the Guide module
   with its issuer.
3. Configure a capable MCP client with an issued bearer and verify user/admin
   operations and denied operations.
4. Roll back by stopping the reference application or removing the provider
   selection; Guide does not need account or configuration migration.
