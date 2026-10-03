# Proposal

## Why

Remote Guide needs an optional access boundary without becoming an identity,
credential, or account service. The boundary must work both behind direct HTTPS
and behind a TLS-terminating proxy, while leaving existing stdio and unauthenticated
remote use unchanged when no provider is selected.

## What Changes

- Add one CLI option, `--auth-provider <provider>`, which selects a trusted
  server-side authentication module. Provider configuration is owned by the
  module's own deployment environment, not by Guide CLI or configuration.
- Start the provider only with a remote transport. It validates request
  evidence, returns request-level `UserAuthorisation` scopes, and can provide
  an opaque HTTPS authentication hand-off.
- Keep Guide opaque to credentials, token format, and principals. Guide uses
  `user` and `admin` access scopes to enforce its bounded operation policy.
- Each protected operation declares its required `user` or `admin` scope
  directly; `admin` is the unrestricted override.
- Keep `set_project`, `switch_project`, normal file callbacks, and
  `update_documents` unprotected. Require `user` for project configuration and
  SQLite ingestion, and `admin` for cloning, permission paths, and global
  configuration.
- Expose request-specific `auth.active`, `auth.authenticated`, `auth.user`, and
  `auth.admin` booleans to templates. With no provider selected, `auth.active`
  is false and all scope predicates are true.

## Specifications

### New specification

- `mcp-authentication`: pluggable remote authorisation lifecycle, decisions,
  hand-off, direct scope declarations, and template availability context.

### Modified Capabilities

- `http-transport`: load a selected provider for either remote HTTP or HTTPS;
  TLS and proxy topology remain deployment responsibility.
- `feature-flags`: require `admin` for global mutation and `user` for project
  flag mutation.
- `guide-project-tools`: retain unprotected binding/selection while protecting
  other configuration mutation and project permission paths.
- `document-store`: protect SQLite ingestion only.
- `request-context`: carry only opaque provider decisions and availability.
- `tool-infrastructure`: retain automatic document updates without auth.
- `template-context`: expose dynamic, request-specific authentication and
  scope booleans.

## Impact

- Affects remote transport startup, operation wrapping, result codes,
  RequestContext, template rendering, and deployment documentation.
- Does not add Guide accounts, passwords, token issuance, a built-in auth
  service, project tenancy, or per-project ACLs.
- `retire-export-metadata` separately removes export tracking. Until it lands,
  the metadata-mutating export operations require user access;
  `add-reference-auth-provider` supplies the reference OIDC pair.
