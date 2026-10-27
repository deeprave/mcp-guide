# Proposal

## Why

Guide still depends on the unmaintained Chevron 0.14.0 renderer. `chevron-ng`
provides a maintained, modern Mustache implementation with an explicit lambda
boundary and an asynchronous rendering API suited to Guide's concurrent MCP
workloads.

## What Changes

- Replace the `chevron` dependency with a released `chevron-ng` version that
  provides the required modern Mustache behaviour and `async_render` API.
- Migrate all Guide rendering paths, including partial and frontmatter value
  rendering, onto the asynchronous renderer without changing agent-visible
  legacy Chevron 0.14.0 behaviour.
- Register callable template extensions exclusively through Chevron's explicit
  `lambdas=` mapping; use `@chevron.section` for section lambdas and
  `@chevron.func` for direct interpolation lambdas where appropriate.
- Preserve Guide's existing partial security boundary, tracked partial
  contributions, rendering limits, error results, and frontmatter semantics.
- Add regression and compatibility coverage for the supported legacy template
  behaviour, async rendering, lambda protocols, and partial rendering.
- Evaluate dynamic tags and inheritance against Guide's document/partial model;
  adopt them only where they simplify an existing, well-tested composition
  path without changing its security or frontmatter rules.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `template-rendering`: Template and partial rendering becomes asynchronous and
  uses an explicit, per-render lambda registry while retaining compatible
  Mustache document behaviour.

## Impact

- Dependency metadata and lockfile, renderer and frontmatter rendering paths,
  template-function implementation, and template rendering tests.
- Existing templates retain their public syntax and output behaviour; migration
  is internal to Guide's renderer integration.
- The selected `chevron-ng` release must be verified to expose the required
  async API before implementation begins.
