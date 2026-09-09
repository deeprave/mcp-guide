## Context

HTTP(S) currently creates FastMCP's ASGI application without a Guide-owned
caller identity, while the tool decorator resolves a session before invoking a
handler. `RequestContext` is the explicit application boundary and deliberately
does not retain raw FastMCP objects. See [proposal.md](proposal.md) for the
motivation and the specification deltas for externally observable behaviour.

Stdio is a local, trusted transport. This change must not change its tool
availability, session handling, or require credentials.

## Goals / Non-Goals

**Goals:**

- Add an opt-in HTTP(S) authentication provider that maps a verified caller to
  a stable identifier and `user`/`admin` scopes.
- Enforce a central, auditable protected-operation inventory before any
  protected tool can create a Session, bind a project, or cause its side effect.
- Carry only credential-free authorisation facts into `RequestContext`.
- Preserve all existing stdio behaviour and unprotected HTTP(S) operations.

**Non-Goals:**

- User account management, self-service credential issuance, OAuth discovery,
  or a web login flow.
- Requiring authentication for read-only or unprotected MCP operations.
- Treating MCP session IDs, project roots, or client metadata as identity.
- Changing document-root semantics beyond preventing unauthorised
  `update_documents` execution.

## Decisions

### 1. Use a server-owned authentication provider only for HTTP(S)

`ServerConfig` will resolve an optional, server-owned authentication provider
at startup. Its provider contract accepts HTTP(S) credentials and returns a
stable principal identifier plus immutable scopes, or a non-revealing rejection.
The initial provider will use configured bearer credentials; the configuration
surface must accept secret references rather than placing credential values in
project configuration or feature flags.

When no provider is configured, HTTP(S) remains unauthenticated. The transport
will identify that state explicitly rather than treating an absent credential as
a `user` or `admin` identity. Stdio is marked trusted by its transport and
never invokes the provider.

Alternatives considered:

- **Require authentication for every HTTP(S) deployment:** rejected because the
  requested deployment model retains a useful public, unprotected surface.
- **Use project configuration for credentials:** rejected because credentials
  are server secrets and project configuration is mutable by the very callers
  this change restricts.
- **Add OAuth now:** rejected as disproportionate to scoped server access and
  because it adds account and discovery flows outside this change.

### 2. Declare required scope on tool registration

Extend the tool registration metadata with an optional required scope. The
registry will provide the authoritative inventory of protected operations:

| Scope | Initial operations |
| --- | --- |
| `user` | Project binding, selection, cloning, all persisted project-configuration mutation (including project feature flags), and `send_file_content` calls that request SQLite document ingestion. |
| `admin` | Global feature-flag mutation, `update_documents`, and `export_content`. |

The wrapper will authorise a protected tool after argument validation but before
entering `request_context_scope`. Scope metadata may include a small
validated-argument predicate: `send_file_content` requires `user` only when
its document-ingestion metadata requests the SQLite write. This prevents an
unauthorised `set_project` request from minting a session or binding a root,
without breaking unprotected file-content callbacks. `admin` implies `user`;
no other scope hierarchy exists in this change. Adding a protected operation
will require an explicit registry declaration and a test, rather than relying
on `requires_project=False` or handler-local checks.

Alternatives considered:

- **Authorise inside each handler:** rejected because it is easy to omit, and
  some handlers have effects before their current internal validation path.
- **Infer privilege from `requires_project`:** rejected because bound-project
  reads and unbound discovery operations are not equivalent to administration.

### 3. Propagate authorisation facts without credentials

The HTTP(S) ASGI boundary will use supported FastMCP/ASGI extension points to
validate credentials before MCP dispatch. It will attach only a small immutable
authorisation record—transport kind, principal identifier when authenticated,
and scopes—to the request passed into Guide's request adapter. The adapter will
copy that record into `RequestContext`; no handler will receive headers, bearer
tokens, or a raw ASGI request.

The standard error result will distinguish authentication-required from
insufficient-scope without identifying the expected credential, token state, or
available privileged operations. Authorisation failures are logged with a
redacted principal/transport outcome suitable for operations diagnostics.

### 4. Preserve compatibility by making policy transport-aware

The authorisation helper receives an explicit transport classification. For
stdio it immediately permits all operations. For HTTP(S), an operation with no
required scope is permitted regardless of caller authentication; an operation
with a required scope needs a validated principal whose scopes satisfy that
requirement. This makes the stdio exemption a single, testable rule rather than
a set of exemptions scattered through tools.

## Risks / Trade-offs

- **A tool may be omitted from the protected-operation inventory** → make
  required scope visible in registry metadata and add a regression test that
  asserts the complete initial scope map.
- **Credential configuration is accidentally logged or persisted** → keep raw
  credentials outside project configuration and redact values in parsing,
  diagnostic, and error paths.
- **FastMCP request integration changes between versions** → use only supported
  HTTP/ASGI hooks and cover the boundary with real HTTP integration tests.
- **A reverse proxy already authenticates callers** → document the supported
  provider boundary so deployments can map trusted proxy identity without
  forwarding an unchecked caller-controlled header.
- **Existing remote clients rely on privileged unauthenticated calls** →
  authentication is disabled by default; enabling it is an explicit deployment
  change with a documented rollback path.

## Migration Plan

1. Release with authentication disabled by default and no project-config
   migration.
2. Document server credential configuration, scope assignment, and the
   protected-operation inventory for HTTP(S) deployments.
3. Deployers enable the provider, assign at least one recovery `admin`
   principal, and verify an unprotected request, a `user` project mutation, and
   an `admin` server mutation before relying on the boundary.
4. To roll back, remove the provider configuration and restart the HTTP(S)
   server; no persisted project data or stdio clients require migration.
