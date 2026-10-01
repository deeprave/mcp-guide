## Why

Guide exposes an MCP surface that can alter process-wide configuration, project
configuration, installed documents, stored documents, and exported content.
Remote deployments need a way to identify a caller and apply externally owned
access policy before those operations run. Guide must not become an identity
provider, token issuer, or account-management service to provide that boundary.

## What Changes

- Add an optional, CLI-selected authentication-provider module for remote MCP
  transports. Its absence preserves current unauthenticated behaviour; its
  presence enables scope checks for explicitly protected operations.
- Start and stop the provider with the remote transport. The provider may
  validate bearer credentials, authenticate through an external service, watch
  policy or revocation updates, and provide an HTTPS handoff for an
  unauthenticated protected operation.
- Keep Guide agnostic to credential format and contents. Only a stable
  principal identifier and immutable scopes may enter Guide's request context.
- Support direct TLS and explicitly configured trusted-proxy deployments. A
  proxy assertion is trusted only when the Guide endpoint is not directly
  reachable and the proxy strips caller-controlled identity headers.
- Require the `user` scope for project-administration operations, including
  creating, selecting, cloning, and changing project configuration.
- Require the `admin` scope for server-wide administration, including changing
  global feature flags and updating installed documentation.
- Require the `admin` scope for document export and make the protected-operation
  inventory explicit, so further privileged mutations cannot be added by
  convention alone.
- Apply one central protected-operation policy at tool, resource, and prompt
  boundaries before session creation, project binding, sensitive reads, or
  side effects. The initial protected inventory remains project administration
  and SQLite ingestion (`user`), plus global flags, document updates, and
  exports (`admin`); `admin` implies `user`.
- Document that principal scopes are not a project tenancy model. A later
  change must add server-generated project identities and per-project access
  control before shared multi-user project hosting is supported.

## Capabilities

### New Capabilities
- `mcp-authentication`: pluggable remote authentication lifecycle,
  authorisation decisions, authentication handoff, and protected-operation
  policy.

### Modified Capabilities
- `http-transport`: load a CLI-selected provider for direct-TLS or trusted
  proxy remote ingress.
- `feature-flags`: require `admin` scope for global feature-flag mutation when
  provider-backed policy is active.
- `guide-project-tools`: require `user` scope for project administration and
  project-configuration mutation when provider-backed policy is active.
- `document-store`: require `user` scope before provider-backed remote document
  ingestion writes to SQLite.
- `request-context`: expose only a provider decision's immutable,
  credential-free principal and scopes.
- `tool-infrastructure`: require `admin` scope for `update_documents` when
  provider-backed policy is active.
- `knowledge-export`: require `admin` scope for `export_content` when
  provider-backed policy is active.

## Impact

- Affects CLI configuration, remote transport startup, ASGI integration,
  request-context propagation, operation registration, error responses, and
  deployment documentation.
- Affects global feature-flag tools, project-management and configuration tools,
  document updates, and exports; read-only and otherwise unprotected tools retain
  their existing unauthenticated behaviour.
- Does not add Guide accounts, credential issuance, a built-in credential
  store, or a web login flow.
- Does not make path hashes a remote project identity or add per-project ACLs.
- Requires provider lifecycle, transport, authorisation-boundary, and
  end-to-end tests using provider fixtures rather than production credentials.
