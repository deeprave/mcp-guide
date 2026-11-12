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
- Make unbound delivery an explicit skill-availability opt-in:
  `allow-unbound: true` packages are discoverable before binding; all other
  packages remain project-dependent and are added once a session is bound and
  satisfies their requirements.
- Revise Git skills so their generic delivery guidance is available unbound and
  their configured policy instructions are rendered only after project binding.
- Return the standard skill catalogue for the current interaction without
  requiring Guide's opaque `session_id`; a client can refresh `skills/list`
  after binding to obtain the expanded catalogue.
- Preserve `guide://$` retrieval, `list_skills`, and `use_skill` as Guide
  compatibility surfaces.
- Retain Guide's `notifications/skills/list_changed` refresh notification and
  emit it after a client binds, so clients that support it can refresh the
  newly expanded catalogue. Standard clients can also refresh explicitly.

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
