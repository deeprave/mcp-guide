# Design

## Context

Guide currently discovers package-shaped skills from `_skills/**/SKILL.md`,
renders them through the normal resource resolver, and offers them through
`guide://$`, `list_skills`, and `use_skill`. Its separate negotiated endpoint
uses the private `io.uniquode/mcp-guide-skills` extension, requires an opaque
Guide session identifier, and only works after project binding.

SEP-2640 standardises `io.modelcontextprotocol/skills`, `skills/list`, and
`skills/get`. It expects skill resources to use `skill://` URIs. Guide's
rendered templates vary by interaction and project, so their contents cannot
honestly be described by one static resource manifest.

## Goals / Non-Goals

**Goals:**

- Give standard MCP clients a catalogue before project binding and a
  project-aware catalogue after it.
- Reuse the existing discovery, requirement filtering, rendering, elicitation,
  and package-containment paths rather than create a second skill system.
- Retain Guide's existing resource and tool interfaces while replacing the
  private negotiated protocol.

**Non-Goals:**

- Change the content or delivery semantics of existing `guide://$` skills.
- Implement the optional SEP-2640 `resources/directory/read` operation or
  expose a template-filesystem-derived public resource tree.
- Require generic clients to act on a Guide refresh notification; the standard
  has no skills-list-changed notification.
- Provide a static hash manifest for rendered skill packages.

## Decisions

### Use the official extension as the sole negotiated skills surface

Register `io.modelcontextprotocol/skills` for modern-protocol sessions and
retire the global `mcp-skills` startup flag. Replace the private method schemas
with the standard `skills/list` and `skills/get` schemas. Suppress the
extension from legacy initialisation in the same way as other modern-only
extensions.

Keeping both extension identifiers would preserve a private discovery protocol
that standard clients cannot use and duplicate lifecycle logic. Guide retains
its existing refresh notification as supplementary compatibility behaviour;
legacy and modern non-negotiating clients retain `guide://$` skills.

### Render skill references for the negotiated capability

Add a `{{#skill}}` section lambda alongside `{{#resource}}`. It accepts a
public skill identity and emits `skill://<identity>/SKILL.md` only when the
current client negotiated `io.modelcontextprotocol/skills`; otherwise it emits
`guide://$<identity>`.

The capability decision must be available in the request's template context.
Protocol revision alone is insufficient because a modern client can decline or
not implement the extension. The lambda does not accept an entrypoint path:
`SKILL.md` is appended exactly once, which keeps generated references
canonical.

### Separate discovery from project requirement evaluation

Refactor package discovery into a metadata catalogue that is safe to build
without a bound project. Add `allow-unbound` frontmatter: only an explicit
`true` allows an unbound catalogue entry; omitted and false values require a
bound project. Once bound, apply the existing `requires-*` frontmatter checks
against the project's effective flags.

This deny-by-default opt-in protects packages that interpolate project
paths, policies, or workflow state. Inferring unbound safety from a package's
current template content would be brittle and could change as a template
evolves.

### Give eligible Git skills an unbound rendering branch

Mark the Git package entrypoints as `allow-unbound: true` after separating
their generic delivery directives from selected project policies. The unbound
branch provides safe Git guidance without tracker, delivery, or policy
assumptions; the bound branch adds those project-selected partials.

This makes useful generic Git guidance discoverable during initial connection
without presenting empty policy partials or claiming a repository's configured
delivery rules before Guide has bound that repository. Other project-aware
skills remain hidden until a concrete unbound use case is designed.

### Give standard skills a virtual, stable resource namespace

Expose a skill named `example` as `skill://example/SKILL.md`, irrespective of
its source-directory layout. Map package-member URIs beneath that root to the
existing package resolver, preserving its rendering and path-containment
checks. The frontmatter `name` remains the public identity, as it is today.

Using the source tree path would make a public URI depend on an implementation
layout and would make flattened names such as `git-commit` awkward to consume.

### Declare rendered resources as dynamic

Return standard skill entries with `resources: "dynamic"`. The entrypoint and
explicitly addressed public members remain available through standard resource
reads, but Guide does not advertise stale sizes or digests for output that
changes with the active project, flags, policies, and template context.

A per-session static manifest was considered. It adds cache invalidation and
integrity bookkeeping while still becoming invalid whenever project settings
or templates change. Dynamic resources are the standard representation for
this server-generated content. Do not implement `resources/directory/read`:
the server's template tree can contain Mustache sources, partials, and future
helpers that are not public skill resources. A future directory feature needs
an explicit virtual public-resource inventory rather than a filesystem walk.

### Refresh after binding

The interaction's active session supplies binding state implicitly; standard
calls do not accept Guide's opaque `session_id`. Before binding, `skills/list`
returns only explicitly unbound-safe skills. After binding, a subsequent
`skills/list` sees the expanded effective set immediately.

Guide also emits its existing `notifications/skills/list_changed` notification
after binding when the standard Skills extension is negotiated. This preserves an
immediate refresh signal for clients that already understand it, without
claiming that generic SEP-2640 clients are required to act on it. A generic
resource notification was rejected because it would not establish a
skills-refresh contract.

## Risks / Trade-offs

- [Clients do not support Guide's refresh notification] → They retain the
  unbound-safe view until they choose to call `skills/list` again; Guide keeps
  its own `guide://$` discovery guidance for clients that need it.
- [Existing packages unexpectedly appear before binding] → Default
  `allow-unbound` to false and explicitly mark only packages whose rendered
  instructions are safe and useful unbound.
- [A client attempts a known `skill://` URI before it is eligible] → Enforce
  the effective catalogue for both `skills/get` and resource reads.
- [The standard evolves while its extension is beta] → Keep the protocol
  adaptation isolated in the extension and use the MCP SDK's current schemas
  where they are available.

## Migration Plan

1. Replace the private negotiated extension, remove `mcp-skills`, and update
   skill package metadata.
2. Register the standard extension only for modern-protocol negotiation and
   render `guide://$` skill references for other clients.
3. Retain Guide URI and tool interfaces without a compatibility deadline.

