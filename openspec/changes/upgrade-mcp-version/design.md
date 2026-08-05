## Context

`mcp-guide` currently exposes a FastMCP server through custom stdio and HTTP
wrappers. Its application state assumes a durable client connection: a task-local
`Session`, a weak registry keyed by `MiddlewareServerSession`, bootstrap context
variables, and a `server.py` monkeypatch of FastMCP's private message handler allow
the server to request roots and react to roots notifications.

MCP protocol revision `2026-07-28` and its v2 SDK model make request negotiation,
request context, and multi-round-trip state explicit. The authoritative local schema
copy is in [`../../std/mcp-schema-2026-07-28.ts`](../../std/mcp-schema-2026-07-28.ts)
and the detailed repository impact analysis is in `analysis.md`. This is an
architectural migration, not a package-version-only change.

## Goals / Non-Goals

**Goals:**

- Support MCP protocol revision `2026-07-28` through supported Python SDK/FastMCP
  APIs, with an explicit revision-negotiation and compatibility policy.
- Introduce a framework-neutral request context that makes project resolution,
  client metadata, and state ownership explicit.
- Eliminate private MCP/FastMCP monkeypatches and connection-object dependencies.
- Preserve guide tools, prompts, resources, rendering semantics, and project safety
  across stdio and Streamable HTTP where the modern protocol provides equivalents.
- Make stateful interactions, background instruction delivery, and project-scoped
  task lifecycle safe under concurrent and stateless requests.

**Non-Goals:**

- Redesign guide domain behavior, project configuration format, templates, or the
  workflow model except where context/state ownership requires it.
- Promise support for every historical MCP protocol revision.
- Add new product capabilities unrelated to the MCP v2 migration.
- Implement this migration in this proposal phase.

## Decisions

### 1. Target the date-stamped protocol revision, not a fictitious wire `2.0.0`

The compatibility target is MCP `2026-07-28`; "v2" identifies the SDK migration
line. The server will negotiate supported revisions and reject unsupported requests
through the selected SDK's standard mechanism.

**Rationale:** the upstream schema defines date-stamped protocol revisions. Treating
`2.0.0` as a wire value would create invalid negotiation behavior.

**Alternative considered:** only increase FastMCP's version and retain current
initialization assumptions. Rejected because the private connection/session coupling
is the primary incompatibility.

### 2. Place a framework-neutral request-context adapter at the protocol boundary

Introduce an application `RequestContext` assembled by a transport/SDK adapter. It
will expose: negotiated revision, request identity, client/agent data, roots, selected
project identity, safe request-state access, and a narrowly defined response metadata
builder. Application services will not receive raw FastMCP contexts.

**Rationale:** this confines SDK API churn to a small adapter and lets tools,
resources, rendering, and session services be tested without a live transport.

**Alternative considered:** change all callers directly to the new FastMCP context.
Rejected because the current code already has many FastMCP-context call sites and
would remain tightly coupled to a framework-specific request shape.

### 3. Replace connection-bound sessions with explicit durable and interaction state

Project configuration remains durable storage. Request-specific data lives in
`RequestContext`. Cross-request interaction state, only when needed, is serialized
as integrity-protected and expiry-bound protocol request state, with server-side
indirection permitted for large or sensitive values. The state must be bound to the
available principal/client scope and the request context it authorizes.

An explicit state owner key will partition pending instructions, rendering caches, and
project-scoped task data. A process-global service may coordinate locks and timers,
but it may not infer the recipient from `ContextVar` or a raw SDK connection object.

**Rationale:** it meets stateless execution while preventing instruction or project
data from crossing clients or projects.

**Alternative considered:** retain a server-memory map keyed by transport session ID.
Rejected as the primary model because it cannot satisfy stateless requests,
multi-process deployment, or protocol request-state integrity requirements.

### 4. Treat roots as request input, not a server-pulled subscription

Project binding will use roots supplied with a request, a valid round-tripped selected
project state, or explicit `set_project`. The server will remove its private
`roots/list_changed` handler and will never call a client roots API from background
code. It will not use server `PWD` to identify a remote client's project.

**Rationale:** v2 removes the legacy server-to-client request route relied on today.
The source of project identity becomes visible and testable.

**Alternative considered:** emulate roots notifications by retaining the private
FastMCP handler patch. Rejected because it preserves the unsupported dependency this
migration is intended to remove.

### 5. Create one public result adapter for modern MCP content and metadata

Keep domain-level `Result` and rendered-content objects independent. A single adapter
will convert them to SDK-native tool, prompt, and resource responses, preserving
instruction dispositions and `additional_agent_instructions`. It will attach cache
hints only when the response is actually safe to cache, with conservative defaults.

**Rationale:** stringifying result JSON before handing it to FastMCP hides protocol
semantics and makes cache metadata and multi-round-trip state difficult to express.

**Alternative considered:** preserve JSON-string responses and layer metadata in
templates. Rejected because protocol metadata belongs in the protocol result, not
rendered user content.

### 6. Use a compatibility spike before selecting concrete package APIs

The first implementation task will test the currently available Python MCP/FastMCP
packages against the copied schema's required operations. It will record the selected
versions and supported APIs before the entry-point rewrite begins.

**Rationale:** package releases may not align one-to-one with the standard and the
repository must avoid designing against an assumed API.

**Alternative considered:** pin an unverified dependency version in this proposal.
Rejected as premature and likely to produce a migration plan tied to non-existent or
incomplete APIs.

## Risks / Trade-offs

- **[SDK/API availability differs from the protocol]** -> Run the compatibility
  spike first; do not merge entry-point migration until required modern operations
  are exercised against the selected packages.
- **[State token replay or substitution]** -> Sign, expire, and bind state to the
  available principal and request authorisation scope; test tampering and replay.
- **[Loss of roots-change responsiveness]** -> Refresh only from supplied request
  data or explicit selection; document changed client expectations and add tests for
  project switches on the next request.
- **[Instruction leakage across concurrent requests]** -> Partition queues and
  caches by explicit owner/project keys; add concurrency/isolation tests.
- **[Legacy client disruption]** -> Decide compatibility policy before release;
  provide an opt-in bounded bridge only if required and test it separately.
- **[Large migration blast radius]** -> Migrate through an adapter with contract
  tests, preserving domain services until each transport surface is verified.

## Migration Plan

1. Add protocol fixtures, package compatibility spike, and a documented selected
   dependency/revision matrix. No legacy behavior is removed at this point.
2. Implement and test the request-context and state-token boundary alongside current
   domain services.
3. Move stdio and Streamable HTTP to the v2-supported entry points and validate
   discovery, negotiation, errors, and response metadata.
4. Migrate tools, prompts, guide resources, result conversion, rendering context,
   and no-project behavior onto the adapter.
5. Migrate TaskManager delivery, cache ownership, and project lifecycle; remove
   session registry/bootstrap state/private-handler code only after equivalent
   behavior is covered.
6. Run interoperability, security, concurrency, and full regression suites. Release
   as a documented breaking protocol upgrade or enable an explicitly scoped legacy
   bridge if the compatibility decision requires one.

Rollback: retain the prior released package version and configuration while the v2
release is staged. After persisted request-state formats are introduced, make them
versioned and ignore unknown versions safely so rollback does not deserialize v2
state as legacy state.

## Open Questions

- Which Python MCP/FastMCP versions fully expose the v2 APIs needed for stdio,
  Streamable HTTP, discovery, and multi-round-trip input?
- Which authentication/principal data is available in stdio and HTTP deployments for
  state-token binding, and what server-side state store is required?
- Is a legacy protocol bridge required for any supported clients, and how long will
  it be maintained?
- Which current uses of client roots, sampling, elicitation, and subscriptions are
  exercised in production clients?
- Which guide responses can safely declare cache metadata, and at what scope/TTL?
