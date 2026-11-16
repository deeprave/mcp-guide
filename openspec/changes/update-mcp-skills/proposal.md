# Proposal

## Why

Guide already exposes packaged skills, but its negotiated skills endpoint is a
private extension that requires a bound project and cannot be consumed through
the MCP Agent Skills standard. Aligning it with SEP-2640 lets compatible hosts
discover and retrieve Guide skills through the standard protocol while
preserving Guide's project-aware delivery.

## What Changes

- Replace the private `io.uniquode/mcp-guide-skills` protocol surface with the
  standard `io.modelcontextprotocol/skills` extension and its `skills/list`
  and `skills/get` operations.
- Retire the `mcp-skills` feature flag: standard skills delivery is always
  available to modern-protocol clients, while legacy and non-negotiating
  clients retain the Guide URI surface.
- Publish Guide skill packages through standard `skill://` resources, including
  their rendered entrypoints and accessible package members.
- Add a `{{#skill}}` template section that renders a canonical skill URI for a
  negotiated Skills client and a `guide://$` reference otherwise.
- Make skill discovery available before binding: skills requiring only project
  binding remain discoverable with a concise binding notice, while skills with
  additional requirements appear only after binding satisfies them.
- Use `project-bind: true` in skill frontmatter to declare that binding-only
  prerequisite without treating it as a project feature flag.
- Revise Git skills so their generic delivery guidance is available unbound and
  their configured policy instructions are rendered only after project binding.
- Add `depth` selection to workflow review: quick uses one lighter reviewer,
  standard uses one heavier reviewer, and thorough uses both before the
  orchestrator returns one combined review.
- Store review and pull-request triage records in Guide's shared user cache,
  using project-and-issue keys when bound and canonical provider/repository/PR
  keys when unbound, without migrating temporary existing review artefacts.
- Return the standard skill catalogue for the current interaction without
  requiring Guide's opaque `session_id`; a client can refresh `skills/list`
  after binding to obtain the expanded catalogue.
- Preserve `guide://$` retrieval, `list_skills`, and `use_skill` as Guide
  compatibility surfaces.
- Retain Guide's `notifications/skills/list_changed` refresh notification and
  emit it when rebuilding detects an effective catalogue change. Standard
  clients can also refresh explicitly.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guide-url-skills`: Replace the private negotiated skills protocol with
  standards-based skill discovery and retrieval, including unbound and
  project-dependent availability.

## Impact

- Affects the MCP extension registration and `mcp_skills_extension` transport,
  skill discovery metadata, resource serving, and skill package frontmatter.
- Changes the negotiated extension identifier and result schema for clients
  using the experimental private endpoint.
- Retains the existing Guide URI and tool interfaces for current clients.
