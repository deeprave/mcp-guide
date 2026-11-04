## Why

Elicitation preflight currently merges delivery properties from declared partials into the final response even when those partials are not rendered. This overrides conditional rendering: `guide://_status` declares `user/information` but returns `agent/instruction` from skipped setup partials.

## What Changes

- Restrict preflight to discovering and resolving elicitation inputs, using `requires-*`, `includes`, and supporting context only as needed.
- Clear unrelated frontmatter at the boundary where preflight has resolved its needs; do not carry response metadata into rendering.
- Derive all final response metadata, including disposition, instruction and cache policy, exclusively from the rendering path and its actual contributors.
- Apply this separation across command and skill entrypoints and audit all shared preflight consumers.
- Preserve shared forms, frontmatter-only form declarations, eligibility checks and resolved input delivery to rendering.
- Replace tests and documentation that deliberately preserve delivery headers from preflight-only partials.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `template-rendering`: Separate elicitation preflight state from rendered delivery properties and prevent skipped partials from contributing response metadata.
- `template-elicitation`: Limit property-only preflight partials to elicitation contributions while retaining eligibility and discovery behaviour.

## Impact

Shared preflight collection in `render/template.py`, document property composition, command dispatch in `prompts/guide_prompt.py`, skill delivery in `tools/tool_resource.py`, associated behaviour tests and authoring guidance. No new dependencies or response fields. Existing working changes for `fix-elicitation-forms` must be preserved; this proposal captures a distinct correction and does not implement it.
