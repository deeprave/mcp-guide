## Context

Frontmatter includes are interpreted in `render_template_content`, then passed
to the partial loader with a base directory. The loader currently accepts
absolute paths and uses path resolution before reading the extension-resolved
file. That path bypasses the document-root resolver required for ordinary
document reads. Existing command templates intentionally use parent-relative
includes, so lexical rejection of every `..` component would break valid
composition.

## Goals / Non-Goals

**Goals:**

- Give every filesystem-backed frontmatter partial load a single canonical
  containment check against the document root.
- Preserve valid relative includes, including nested `..` references that
  canonically remain in root.
- Ensure no unsafe candidate is read, rendered, or contributes frontmatter,
  while logging the same non-fatal warning-and-omit outcome used for unsafe
  template paths.
- Keep renderer failures local to the rejected partial so safe template output
  remains available.

**Non-Goals:**

- Altering Mustache partial syntax, extension precedence, or ordinary document
  discovery.
- Restricting pre-rendered in-memory partials, which have no filesystem read.
- Treating the template's directory as the security boundary; it remains only
  the relative-reference base.
- Changing document-root configuration or authorising access outside it.

## Decisions

### 1. Resolve from the including template, then enforce canonical containment

The partial loader will accept a frontmatter reference, the directory of the
template that includes it, and a document-root resolver supplied by the calling
request path. This is exclusively a server-side document-root containment
operation: it SHALL NOT use `LazyPath.client_resolve()` or any client
filesystem semantics. Relative references are always resolved from that
including template's directory; they are never relative to the process
directory, document root, or another partial. Absolute references are allowed
only when the final canonical candidate remains in document root.
Home-anchored (`~` or `~user`) and environment-variable expansion syntax are
invalid template path forms and are rejected without expansion.

For a permitted reference, the loader derives the partial filename separately:
frontmatter names a partial without its leading underscore and the loader
selects the corresponding underscore-prefixed filename. Any explicit extension
or extension search is independent of the reference base and containment
calculation. The filename prefix is significant beyond loader convention:
ordinary command and category discovery excludes underscore-prefixed files, so
partials cannot be selected as normal documents by a category pattern. It
validates the final resolved candidate through the supplied resolver before
opening it.

This permits a template at `some_category/subcategory/somefile.md.mustache` to
include `../partials/some_partial.mustache`, resolving it as
`some_category/partials/_some_partial.mustache` when it remains within the
configured root. Validating only the initial joined path is
insufficient because extension resolution and symlinks can change the eventual
file target.

Alternatives considered:

- **Reject all parent components:** rejected because existing nested command
  templates use in-root `../` composition.
- **Check string prefixes before reading:** rejected because path spelling and
  symlinks make lexical containment unsafe.
- **Use the template directory as the root:** rejected because it both blocks
  valid shared partials and permits traversal to sibling host paths.

### 2. Reuse the established document-root resolver as the authority

Filesystem-backed renderer paths will receive the existing document-root
resolver explicitly rather than reading a document-root path from `Session`,
current working directory, or raw transport state. Every extension candidate
will use that resolver, which canonicalises and validates containment. Direct
renderer tests that exercise filesystem includes will provide a bounded test
resolver; rendering without filesystem includes retains its existing API
behaviour.

This keeps partial resolution aligned with the project’s explicit
request-context boundary and prevents a convenience fallback from reviving an
unbounded host-path read.

### 3. Treat unsafe includes like unsafe template paths, not template failures

Introduce a specific safe-resolution failure that carries no resolved host path
or file content. The renderer will log a concise warning, omit the unsafe
partial from the rendering set, and continue processing other declared partials
and the parent template. The failure must occur before `read_text`, frontmatter
parsing, cache-policy parsing, or partial-frontmatter merging.

Alternatives considered:

- **Fail the complete template:** rejected because the current renderer
  tolerates unavailable partials and a malicious optional include must not
  suppress otherwise safe output.
- **Silently ignore it:** rejected because an operator-visible diagnostic helps
  repair templates without revealing a target path or its contents.

### 4. Validate the frontmatter contract at both layers

Frontmatter parsing will identify plainly invalid expansion syntax early, but
will not fail the parent document. The partial loader remains the final
authority and repeats canonical containment after extension lookup, since it is
the only layer that knows the file actually selected for reading. This defence
in depth protects direct loader callers as well as the normal renderer path.

## Risks / Trade-offs

- **Callers omit the resolver** → require it whenever a filesystem-backed
  frontmatter partial is requested and add integration coverage for every
  renderer entry point.
- **A symlink changes after validation** → resolve the final candidate
  immediately before the read and keep the check-and-read path narrowly scoped;
  document that ordinary filesystem race guarantees remain outside this change.
- **Legacy home-anchored partials stop rendering** → this is an intentional
  security break; diagnostics identify the invalid include without exposing the
  target.
- **Tests rely on direct loader access to arbitrary temporary paths** → update
  them to provide an explicit bounded root and replace the old home-anchored
  success case with rejection coverage.

## Migration Plan

1. Release the containment check with diagnostics for rejected partials.
2. Replace affected bundled or deployment templates with relative in-root
   references before enabling the release in production.
3. If a valid template is rejected, move the shared partial under the document
   root and update its reference; rollback consists of reverting the release,
   not relaxing the root boundary.
