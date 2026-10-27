# Design

## Context

Guide's asynchronous rendering entrypoint currently calls the synchronous
Chevron 0.14.0 renderer. Template callable functions are mixed into the normal
context mapping, and several section functions depend on Chevron's historic
two-argument callback protocol. Renderable frontmatter separately calls the
synchronous renderer. See `proposal.md` for the motivation and the
`template-rendering` delta for behaviour requirements.

## Goals / Non-Goals

**Goals:**

- Use a maintained renderer release with the required asynchronous API.
- Establish one async rendering boundary for template bodies, partials, and
  renderable frontmatter.
- Move Guide extensions to an explicit, per-render lambda registry and the
  renderer's modern decorated extension protocols.
- Prove legacy output, partial contribution tracking, error handling, limits,
  and security behaviour before replacing the dependency.

**Non-Goals:**

- Redesign Guide's template language, context namespaces, frontmatter schema,
  or document composition model.
- Enable filesystem partial lookup or relax the existing document-root boundary.
- Adopt dynamic tags or inheritance merely because the renderer supports them.

## Decisions

### Gate the upgrade on a released async API

The dependency change will select the first suitable released `chevron-ng`
version only after verifying its package API and behaviour in a clean
environment. At planning time, the current `0.15.0` public documentation still
describes asynchronous rendering as future work; therefore it is not enough to
implement this change as written.

Pinning the currently published synchronous release and wrapping it with
threads was rejected. It would retain a split rendering model, fail to deliver
async extension support, and create an unnecessary migration later.

### Keep one renderer integration boundary

The existing asynchronous `render_template_content` path will await the new
renderer directly. Renderable frontmatter will become asynchronous and await
the same renderer semantics. Partial discovery, safe source loading, size
checks, contribution tracking, error normalisation, and recommendation
footnotes remain Guide responsibilities surrounding the renderer call.

Separate synchronous helper rendering was rejected because it would make
extension semantics vary by document field and prevent async extensions there.

### Declare extensions explicitly per render

Guide will construct a `lambdas=` mapping for every render. Context values are
data only; Guide extensions are decorated and registered under the supported
names. Section extensions use the renderer's modern section protocol and
direct derived values use its interpolation protocol. Existing extensions that
depend on the historic `render()` callback will be refactored around their
explicit inputs and the current template context rather than preserving an
implicit compatibility callback.

Leaving extensions in the context was rejected because it keeps executable
objects indistinguishable from data and prevents a complete move to the new
renderer contract.

### Treat dynamic tags and inheritance as targeted follow-up opportunities

The implementation will identify existing partial patterns that can be made
clearer with dynamic tags or inheritance. It will adopt one only when a small,
behaviour-backed conversion preserves current frontmatter, partial tracking,
and security semantics. Otherwise these features remain available but unused.

A broad conversion was rejected because it would combine a dependency and
concurrency migration with an unrelated template rewrite.

## Risks / Trade-offs

- [The required published async renderer API is not yet available] → Do not
  begin the dependency replacement; revisit when the release is published.
- [Modern Mustache compliance changes whitespace, lambda, or delimiter edge
  cases] → Capture current Guide rendering behaviour in focused regression
  fixtures before migration and compare after it.
- [An extension conversion changes nested rendering semantics] → Convert each
  extension deliberately, retaining only behaviour that templates exercise and
  covering normal and error paths.
- [Async partials could bypass established safeguards] → Keep all partial
  path validation, source limits, and contribution collection outside the
  renderer and prove them through integration tests.

## Migration Plan

1. Capture legacy behaviour with focused fixtures and identify all current
   renderer and lambda call sites.
2. Verify the selected released `chevron-ng` API, then update dependency and
   lockfile in an isolated change.
3. Convert the common rendering boundary, frontmatter rendering, and extension
   registry; migrate extensions incrementally.
4. Run the full template, security, and integration suites; compare the
   established legacy fixtures and inspect the diff for unrelated template
   changes.
5. Roll back by restoring the previous dependency and renderer call boundary if
   compatibility or security validation fails before release.
