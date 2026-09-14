## Why

Template partial frontmatter was intended to affect the disposition of the rendered parent: a contributing partial can change content from `user/information` to `agent/instruction`.  The current rendering path retains partial frontmatter for instruction processing but resolves the parent disposition from its own frontmatter, and pre-rendered policy partials discard their frontmatter entirely.  This can make consumers handle rendered content incorrectly, including status and command output that depends on instruction disposition.

## What Changes

- Replace the parallel cache and disposition aggregation paths with a shared document-properties model for individual documents, rendered partials, and multi-document deliveries.
- Resolve a rendered document's effective disposition from the parent and every partial that actually contributes content, using the established disposition precedence.
- Preserve the frontmatter or resolved disposition of pre-rendered `policies:` documents so policy partials participate under the same rules as ordinary `includes` partials.
- Ensure content, prompt, command, and status delivery paths preserve the resolved disposition rather than reverting to the parent declaration.
- Add behaviour-level coverage for ordinary partials, policy partials, skipped partials, and a status or command path that consumes the resulting disposition.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `template-rendering`: Resolve parent disposition from all rendered partial contributors, including pre-rendered policy documents.

## Impact

- Rendering, partial-tracking, and multi-document aggregation code in `src/mcp_guide/render/` and `src/mcp_guide/content/utils.py`.
- Content and prompt/command result paths that consume `RenderedContent` disposition.
- Template-rendering specifications and behavioural tests.
