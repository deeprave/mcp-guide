## Why

Frontmatter-controlled Mustache partials bypass the document-root containment
rules used by ordinary document loading. A stored template can therefore cause
rendering to read an underscore-prefixed partial outside the configured
document root through an absolute, home-expanded, traversal, or symlinked path.

## What Changes

- Resolve frontmatter partial references relative to the rendering template
  while enforcing canonical containment within the configured document root.
- Reject absolute and home-anchored partial references and reject any relative
  reference whose final, extension-resolved target escapes the document root.
- Preserve valid nested and parent-relative includes that resolve inside the
  document root, including existing command partial layouts.
- Prevent unsafe partial references from being read or rendered while allowing
  the containing template and other valid partials to render normally.
- Add regression coverage for traversal, absolute, home-anchored, and symlink
  escape attempts, as well as in-root relative partial resolution.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `template-rendering`: constrain frontmatter partial loading to canonical
  targets inside the configured document root.
- `frontmatter-processing`: validate the `partials` frontmatter field against
  the safe partial-reference contract.

## Impact

- Affects template rendering, frontmatter include validation, partial loader
  APIs, and tests around command/template composition.
- **BREAKING:** templates whose partial references resolve outside the document
  root will no longer render that partial.
- Does not change ordinary document loading or valid in-root relative includes.
