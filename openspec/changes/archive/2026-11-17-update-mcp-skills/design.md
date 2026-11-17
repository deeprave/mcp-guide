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

- Give standard MCP clients an unbound metadata catalogue before or after
  project binding, while allowing known resource reads to use a Guide session
  identifier for bound rendering.
- Reuse the existing discovery, requirement filtering, rendering, elicitation,
  and package-containment paths rather than create a second skill system.
- Retain Guide's existing resource and tool interfaces while replacing the
  private negotiated protocol.

**Non-Goals:**

- Remove existing `guide://$` skill compatibility surfaces.
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

### Render canonical skill references

Add a `{{#skill}}` section lambda alongside `{{#resource}}`. It accepts a
public skill identity and always emits `skill://<identity>/SKILL.md`. Guide's
`read_resource` compatibility surface resolves those URIs for clients that use
it. The lambda does not accept an entrypoint path: `SKILL.md` is appended
exactly once, which keeps generated references canonical.

### Separate discovery from project requirement evaluation

Refactor package discovery into a metadata catalogue that is safe to build
without rendering a template. Discovery loads each package's `FileInfo` and
frontmatter only; it never loads partials, evaluates template sections, or
resolves policies. Before binding, publish every package with no
requirement beyond project binding: packages that need binding identify that
briefly in their description and direct the agent to `{{tool_prefix}}set_project`.
Packages with additional requirements remain unavailable from the standard
unbound catalogue. Guide compatibility catalogue and selection paths continue
to use their request context when resolving effective requirements.

Use `project-bind: true` in package frontmatter to declare the binding-only
prerequisite. It is catalogue metadata, not a project feature flag and not a
`requires-*` condition. A package with this marker and no other unmet
requirements remains discoverable before binding with binding guidance; a
direct unbound read returns the shared no-project result instead of rendering
project-dependent content.

### Render the exceptional unbound variant explicitly

Expose `unbound` as a boolean template-context value when the interaction has
no bound project. Templates use `{{#unbound}}` only for exceptional
unbound-safe or binding-guidance instructions; ordinary bound instructions
remain outside that section. During selected-skill rendering, unbound policy
partials resolve blank automatically, while a bound session resolves its
selected policies through the shared rendering path. Do not infer binding from
an empty project object, paths, or feature flags, and do not use a `session`
section because an interaction session may exist before project binding.

### Give eligible Git skills an unbound rendering branch

Give the Git package entrypoints an unbound branch after separating their
generic delivery directives from selected project policies. The unbound branch
provides safe Git guidance without tracker or delivery assumptions; policy
inclusions remain ordinary shared template inclusions because unbound policy
resolution supplies blank content. A bound session adds its selected policies
through the same shared rendering path.

This makes useful generic Git guidance discoverable during initial connection
without presenting empty policy partials or claiming a repository's configured
delivery rules before Guide has bound that repository.

### Select workflow-review depth explicitly

Give workflow review one `depth` selection for both bound and unbound
rendering. `quick` runs one lighter reviewer, `standard` runs one heavier
reviewer, and `thorough` runs both independently. `thorough` remains the
default. After the independent reviews finish, the orchestrating agent SHALL
combine their outcomes into one review for the user; bound rendering retains
the workflow-aware handling around that result.

### Store review records in shared cache

Add `get_cache_dir()` alongside the existing configuration-path helpers, using
the XDG user-cache location. The cache directory SHALL be an implied runtime
read/write root for every session and exposed as `{{path.cache}}` in both bound
and unbound template contexts. Bound workflow reviews use the Guide project
identity and active issue as their cache key. An unbound pull-request review
uses provider host, immutable repository identity, and pull-request number;
its combined record is stored at
`{{path.cache}}reviews/<provider>/<repository-id>/<pr-number>.json`. This key
also stores pull-request triage state so later bound or unbound triage sees
only new threads. Unbound branch or working-tree reviews have no stable
cross-session identity and return their result directly unless the user names
an output destination. Existing project review and triage documents are
temporary artefacts; do not migrate them into this cache.

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

### Keep catalogue and rendering separate

`skills/list` and `skills/get` use the unbound metadata catalogue only and
never render skill templates. They return dynamic-resource entries describing
the available skills. A `skill://` resource read delegates to the same
selected-skill/member resolver as `guide://$`, so elicitation, policy handling,
containment, and rendering have one implementation. The protocol adapters may
format the result differently, but they do not duplicate skill resolution or
retain rendered skill bytes between requests.

Catalogue URIs remain canonical and session-free. A client that has bound a
Guide session may append its returned `session_id` as a query argument when
reading a known `skill://` resource, allowing modern stateless transport to
resolve that bound Guide session without changing the catalogue entry.

### Refresh after catalogue changes

Standard catalogue calls remain deliberately session-independent. They return
every package with no prerequisite beyond project binding and omit packages
with additional unmet requirements. A client that needs bound rendering adds
its Guide `session_id` to a known `skill://` resource read.

When rebuilding detects that the effective metadata catalogue changed, Guide
emits its existing `notifications/skills/list_changed` notification to the
requesting client when the standard Skills extension is negotiated. This does
not retain per-session catalogue state or require generic SEP-2640 clients to
act on a non-standard refresh signal.

## Risks / Trade-offs

- [Clients do not support Guide's refresh notification] → They retain the
  pre-binding view until they choose to call `skills/list` again; Guide keeps
  its own `guide://$` discovery guidance for clients that need it.
- [A listed skill needs project context] → Its description states that binding
  is required and directs the agent to `{{tool_prefix}}set_project`; templates
  use their `unbound` branch rather than rendering project-derived values.
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

