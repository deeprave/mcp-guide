## Why

Frontmatter-controlled Mustache partials bypass the document-root containment
rules used by ordinary document loading. A stored template can therefore cause
rendering to read an underscore-prefixed partial outside the configured
document root through an absolute, home-expanded, traversal, or symlinked path.

## What Changes

- Resolve relative frontmatter partial references relative to the rendering
  template while enforcing canonical containment within the configured document
  root. Absolute references are permitted only when their final canonical
  target remains within that root.
- Reject home-anchored and environment-variable expansion syntax, and reject
  any relative or absolute reference whose final, extension-resolved target
  escapes the document root.
- Preserve valid nested and parent-relative includes that resolve inside the
  document root, including existing command partial layouts.
- Prevent unsafe partial references from being read or rendered, log a warning
  without exposing the target, and allow the containing template and other
  valid partials to render normally.
- Preserve the partial naming convention: a frontmatter reference names a
  partial without its leading underscore; the loader resolves the corresponding
  underscore-prefixed filename independently of any extension suffix. The
  underscore also keeps partial files excluded from ordinary command and
  category document discovery.
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
