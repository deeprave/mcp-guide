## Why

Guide currently treats every HTTP(S) MCP caller as the same unauthenticated
principal, even for operations that alter process-wide configuration, projects,
the installed document root, or exported document content. Deployments need an
optional authentication boundary that limits those mutations without removing
the useful unauthenticated MCP surface.

## What Changes

- Add optional HTTP(S) MCP authentication that resolves a caller identity and
  its `user` and/or `admin` scopes before a protected operation runs; stdio
  remains trusted and never requires authentication.
- Keep authentication disabled by default and preserve unauthenticated access
  to operations that are not explicitly protected.
- Require the `user` scope for project-administration operations, including
  creating, selecting, cloning, and changing project configuration.
- Require the `admin` scope for server-wide administration, including changing
  global feature flags and updating installed documentation.
- Require the `admin` scope for document export and make the protected-operation
  inventory explicit, so further privileged mutations cannot be added by
  convention alone.
- Return a consistent authorisation failure before a protected operation changes
  state, without disclosing credentials or granting scope from MCP session IDs.

## Capabilities

### New Capabilities
- `mcp-authentication`: optional MCP caller authentication, scope resolution,
  protected-operation classification, and authorisation failure behaviour.

### Modified Capabilities
- `http-transport`: authenticate configured HTTP(S) callers before protected
  MCP application operations are dispatched.
- `feature-flags`: require `admin` scope for global feature-flag mutation.
- `guide-project-tools`: require `user` scope for project administration and
  project-configuration mutation.
- `document-store`: require `user` scope before HTTP(S) document ingestion
  writes to the SQLite store.
- `request-context`: expose an immutable, credential-free caller
  authorisation result to application-boundary checks.
- `tool-infrastructure`: require `admin` scope for `update_documents`.
- `knowledge-export`: require `admin` scope for `export_content`.

## Impact

- Affects HTTP(S) transport setup, request-context identity propagation, tool
  registration/authorisation, configuration, and MCP error responses; stdio
  tool invocation remains unchanged.
- Affects global feature-flag tools, project-management and configuration tools,
  document updates, and exports; read-only and otherwise unprotected tools retain
  their existing unauthenticated behaviour.
- Requires focused authentication/authorisation tests and installation/deployment
  documentation for enabling the optional boundary.
