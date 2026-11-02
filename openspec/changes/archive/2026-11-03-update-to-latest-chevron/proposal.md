# Proposal

## Why

Guide still depends on the unmaintained Chevron 0.14.0 renderer. `chevron-ng`
provides a maintained, modern Mustache implementation with an explicit lambda
boundary and an asynchronous rendering API suited to Guide's concurrent MCP
workloads.

## What Changes

- Replace the `chevron` dependency with a released `chevron-ng` version that
  provides the required modern Mustache behaviour and `async_render` API.
- First validate its synchronous `render` API as a drop-in replacement for
  Guide's Chevron 0.14.0 integration; migrate rendering to async only after
  that compatibility gate passes.
- Then migrate all Guide rendering paths, including partial and frontmatter
  value rendering, onto the asynchronous renderer without changing
  agent-visible legacy Chevron 0.14.0 behaviour.
- Register callable template extensions exclusively through Chevron's explicit
  `lambdas=` mapping; use `@chevron.section` for section lambdas and
  `@chevron.func` for direct interpolation lambdas where appropriate. Retire
  the unused `contains` extension, whose one-value parsing contract did not
  implement its implied containment operation.
- Retire the unused external-highlighter availability probe: `highlight_code`
  always produces a language-labelled Markdown code fence, and Guide no longer
  declares a direct dependency solely for that unused path.
- Preserve Guide's existing partial security boundary, tracked partial
  contributions, rendering limits, error results, and frontmatter semantics.
- Give renderable frontmatter an explicit lambda profile: retain needed
  contextual functions such as `prompt` and `tool_prefix`, preserve `_error`
  diagnostics, and reject `recommend` clearly because it requires an active
  delivery session and rendered-content footnotes.
- Add regression and compatibility coverage for the supported legacy template
  behaviour, async rendering, lambda protocols, and partial rendering.
- Evaluate dynamic tags and inheritance against Guide's document/partial model;
  adopt them only where they simplify an existing, well-tested composition
  path without changing its security or frontmatter rules.
- Upgrade the selected dependency to `chevron-ng` 0.20.0 and adopt its
  opt-in conditional-section and enhanced-iterator facilities in Guide-owned
  templates.
- Add a standalone, repeatable production-template inventory runner with
  curated example contexts and expected output checks, so renderer upgrades
  can exercise shipped templates and partial compositions outside pytest.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `template-rendering`: Template and partial rendering becomes asynchronous and
  uses an explicit, per-render lambda registry while retaining compatible
  Mustache document behaviour.
- `template-support`: `highlight_code` is specified as Markdown code fencing,
  without a Guide-level syntax-highlighting or colour-output path.
- `template-rendering`: Guide-owned templates use the selected 0.20.0
  conditional-section and enhanced-iterator syntax instead of Guide-created
  iterable guard flags and `IndexedList` iteration wrappers.
- `mcp-resources-guide-scheme`: Command URI queries normalise the standard
  short option aliases in the same way as prompt commands.

## Impact

- Dependency metadata and lockfile, renderer and frontmatter rendering paths,
  template-function implementation, Guide-owned templates, the rendering
  context adapter, template rendering tests, and a standalone inventory
  runner.
- Shared command-option normalisation, command URI parsing, and command URI
  documentation.
- Existing templates retain their public syntax and output behaviour; migration
  is internal to Guide's renderer integration.
- The selected `chevron-ng` release must be verified to expose the required
  async API before implementation begins.
