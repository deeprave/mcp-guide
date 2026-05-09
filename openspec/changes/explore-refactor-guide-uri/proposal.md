## Why

The current `read_resource` tool name hides that the implementation is really a
`guide://` URI resolver with two distinct behaviours: content retrieval for
content URIs and command rendering for underscore-prefixed command URIs. This
creates avoidable confusion with MCP's generic resource-reading concepts and
makes it less obvious which entrypoint agents should use when native MCP
resource reads are unavailable.

## What Changes

- Explore whether the guide URI resolver should be exposed under a clearer
  tool name, such as `resolve_guide_uri`, while preserving the existing
  `guide://` URI semantics.
- Decide whether the existing `read_resource` tool should be renamed, retained
  as a compatibility alias, or supplemented by a new preferred entrypoint.
- Keep both URI personalities intact:
  - `guide://_<command>/<args>?<kwargs>` resolves through command rendering.
  - `guide://<category-or-collection>/<patterns>` resolves through guide
    content retrieval.
- Clarify that generic MCP resource reads and the tool entrypoint should share
  the same resolver implementation and return compatible results.
- Update agent-facing wording so the resolver is described by what it does for
  `guide://` URIs, not as an arbitrary MCP resource reader.
- Avoid breaking existing callers unless a deliberate compatibility plan is
  captured in design and tasks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mcp-resources-guide-scheme`: clarify the canonical guide URI resolver
  contract, including whether `read_resource`, `resolve_guide_uri`, or both are
  supported tool entrypoints for the same `guide://` behaviours.
- `documentation`: update user-facing guide URI documentation to explain the
  preferred entrypoint and its relationship to native MCP resource reads.
- `template-support`: update agent instruction text that currently names
  `read_resource` so agents learn the preferred resolver terminology.

## Impact

- Affected code is likely to include `src/mcp_guide/tools/tool_resource.py`,
  `src/mcp_guide/resources.py`, URI resolver tests, and any tool registration
  or tool result naming tied to `read_resource`.
- Affected docs and templates include guide URI documentation and one-shot
  agent instructions that mention the current fallback tool.
- Compatibility risk is concentrated around existing agents or clients that
  already call `read_resource`; the design should decide whether to keep that
  tool as an alias, deprecate it, or leave it unchanged while adding a clearer
  preferred entrypoint.
