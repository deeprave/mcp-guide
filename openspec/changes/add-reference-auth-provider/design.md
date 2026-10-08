# Design

## Context

`add-mcp-authentication` establishes a generic remote provider boundary but
does not prove that an external identity system can satisfy it. This change
adds a reference pair in the same distribution: an optional Guide-side OIDC
module and an independent identity-provider application. See the proposal and
the `reference-auth-provider` requirements for the behaviour contract.

## Goals / Non-Goals

**Goals:**

- Exercise the Guide provider lifecycle, `UserAuthorisation` scope results,
  hand-off, key refresh, and template availability boundary against a real issuer.
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

Place the Guide adapter under the main package as an optional `auth-ref-oidc`
provider entry point. Place the reference identity-provider application in a distinct
namespaced package with its own executable command. Both ship in the
distribution as three delivery components: the adapter plugin, the persistent
reference-provider process, and its administrator command.

The adapter SHALL first connect to its configured issuer at startup. In local
reference-provider mode, a failed connection SHALL cause it to start the
provider process, wait for its discovery endpoint to become available, and
retry. A failed start or readiness check SHALL fail the protected Guide
transport. An adapter that started the process SHALL stop it with the
transport; it SHALL not stop a pre-existing or externally managed issuer.

External issuers remain independently deployed and are never started by Guide.
This preserves one repository and compatible releases while retaining the
operational boundary. An independent repository or distribution remains
possible later if the reference application outgrows this release cadence.

### OIDC module is a resource-server adapter

The `auth-ref-oidc` module discovers issuer metadata and public signing keys, validates
bearer access tokens, and maps provider-owned grants to `AuthScope.USER` and
`AuthScope.ADMIN` in a `UserAuthorisation` result. Guide applies the declared
scope at each protected operation: missing or invalid authentication becomes
`not_authorised`; a valid bearer without the required scope becomes
`forbidden`; and `admin` satisfies `user`. Guide receives neither raw token
content, decoded claims, nor a principal identity as an application-level
authorisation input.

Provider configuration belongs to the module's deployment environment, not an
additional Guide CLI argument or persisted Guide configuration. This preserves
the single provider-selection option and lets credentials remain under the
identity-provider operator's control.

### Encrypted local accounts, standards-based tokens, and API administration

The reference application keeps its user store in SQLite encrypted at rest with
SQLCipher, accessed through SQLAlchemy and a SQLCipher-capable DBAPI. SQLCipher
rather than ORM field encryption protects the complete database and its
journals. The encryption key SHALL come from provider-owned secret
configuration and SHALL not be stored in the database, Guide configuration, or
administrator command arguments.

The store holds Argon2id password verifiers, coarse user/admin grants,
asymmetric signing keys, short-lived access tokens, OIDC discovery metadata,
and JWKS key publication. The administrator command is an API client: it calls
the persistent provider's authenticated management API to create, list, remove,
and grant access to users, and securely set or reset passwords. It does not
open, migrate, or write the SQLite database. The provider owns administrator
authentication and bootstrap, and the management API's exposure is controlled
by provider-owned deployment configuration.

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
- [A local password flow or user store is attacked] → use modern password
  verifiers, encrypted SQLite, external key management, HTTPS, rate limiting,
  generic login failures, short-lived tokens, and no password or token logging.
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
