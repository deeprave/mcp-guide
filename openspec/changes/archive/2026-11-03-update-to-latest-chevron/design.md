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

### Prove synchronous compatibility before asynchronous migration

The dependency change will select a suitable released `chevron-ng` version only
after verifying its synchronous `render` API and Guide's existing template,
partial, frontmatter, and extension behaviour in a clean environment. The
initial migration deliberately retains synchronous execution so that renderer
compatibility is isolated from the concurrency and extension-protocol change.

`chevron-ng` 0.17.0 is the selected release. Its public synchronous
`chevron.render` API accepts Guide's existing template, context, and
in-memory partial mapping arguments. Guide passes `partials_path=None`
explicitly for every synchronous body and renderable-frontmatter render.

The explicit extension registry is also established while rendering remains
synchronous. That keeps the callable-data boundary independent of the later
asynchronous migration and gives the async work a data-only context from the
outset. Once those synchronous boundaries pass, Guide verifies the released
asynchronous API and migrates the shared rendering boundary.

### Adopt Chevron 0.20 extensions deliberately

`chevron-ng` 0.20.0 is the selected final release for this change. Before any
new syntax is enabled, Guide updates only its dependency metadata and lockfile
and runs its standard test suite. This preserves a clean diagnostic boundary
between the dependency update and subsequent Guide template migrations.

Guide then enables `Extension.CONDITIONAL_SECTIONS` and converts its own
iterable truthiness guards to `{{?name}}...{{/name}}`. Conditional sections
render a truthy body once without iterating or changing the active context,
including when a later ordinary section consumes the same streaming source.
This replaces Guide-created scalar guard values used only to suppress a
heading around an iterable.

Guide also enables `Extension.ENHANCED_ITERATORS` and removes the `IndexedList`
context wrapper. Shipped templates use section-scoped `.first`, `.last`, and
the current item `.` rather than Guide-injected `first`, `last`, and `value`
members. The extension also supplies `.index`, `.ordinal`, and `.length` for
future Guide-owned templates without materialising streaming sources.

Guide enables the two named extensions rather than `Extension.ALL`, so future
Chevron extensions cannot silently change Guide's template language. This
reserves `?` for conditional-section syntax in Guide rendering. The migration
is deliberately limited to Guide-owned templates; user templates remain
ordinary Chevron templates but may adopt the documented syntax when rendered
by Guide.

### Keep a standalone production-template inventory check

Pytest remains the test framework for Guide behaviour. In addition, a
standalone inventory runner will discover every shipped renderable template,
render curated production templates and partial compositions through Guide's
public rendering boundary with representative data, and check their declared
expected output. It is an upgrade-acceptance and repeatability tool, not a
pytest source-template test. The runner executes after the dependency-only
upgrade, after conditional sections, and after enhanced iterators so each
stage has an observable compatibility checkpoint.

### Keep one renderer integration boundary

The existing asynchronous `render_template_content` path will await the new
renderer directly. Renderable frontmatter will become asynchronous and await
the same renderer semantics. Partial discovery, safe source loading, size
checks, contribution tracking, error normalisation, and recommendation
footnotes remain Guide responsibilities surrounding the renderer call.

Separate synchronous helper rendering was rejected because it would make
extension semantics vary by document field and prevent async extensions there.

### Declare extensions explicitly per render

Guide constructs a `lambdas=` mapping for every render while the context stays
data-only. Existing extensions that need Chevron's historical render callback
are declared with `@chevron.compat` and await that callback; two-argument
extensions that do not use it are reduced to a one-argument
`@chevron.section` function. Names such as `workflow.contains` remain registry
keys rather than nested callables in the workflow data. Conditional and
wrapper-only callbacks use `@chevron.section`; callbacks that inspect rendered
input for parsing or side effects remain compatibility extensions.

The unused `contains` extension is retired rather than migrated. Its single
template argument could not express both the value to seek and the collection
or string to inspect, and no shipped template invoked it. `workflow.contains`
is a separate, supported workflow-phase predicate and remains registered.

Leaving extensions in the context was rejected because it keeps executable
objects indistinguishable from data and prevents a complete move to the new
renderer contract.

### Give renderable frontmatter a dedicated lambda profile

Renderable frontmatter needs declared extensions because `prompt` and
`tool_prefix` are now interpolation functions rather than ordinary context
values. It must not, however, inherit body-only effects without retaining their
result state.

The frontmatter profile retains the contextual and section extensions that can
produce delivery-field text. It captures `_error` messages and field rendering
failures, preserves successfully rendered sibling fields, and carries those
diagnostics into the final `RenderedContent` result. `recommend` is explicitly
unavailable in frontmatter: it requires an active delivery session to resolve
its target and append a rendered-content footnote. Its use produces a clear
frontmatter authoring diagnostic rather than reverting every renderable field
or leaving raw Mustache text in the delivered metadata.

### Treat dynamic tags and inheritance as targeted follow-up opportunities

The implementation will identify existing partial patterns that can be made
clearer with dynamic tags or inheritance. It will adopt one only when a small,
behaviour-backed conversion preserves current frontmatter, partial tracking,
and security semantics. Otherwise these features remain available but unused.

A broad conversion was rejected because it would combine a dependency and
concurrency migration with an unrelated template rewrite.

The implementation audit found no suitable narrow conversion. Guide's 38
partial call sites use static, author-owned names so their includes can be
validated and loaded before render. The superficially repetitive
issue-tracker policies are separately discoverable documents which deliberately
share an explicit `_provider-common` partial and its frontmatter contribution.
Dynamic selection or an inheritance layout would add a runtime selection path
without removing that document model or simplifying the established output.

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
2. Verify the selected `chevron-ng` synchronous API, update the dependency and
   lockfile, and prove it is a drop-in renderer replacement.
3. Verify the released asynchronous API, then convert the common rendering
   boundary and frontmatter rendering; adapt compatibility callbacks to await
   Chevron's asynchronous render callback.
4. Run the full template, security, and integration suites; compare the
   established legacy fixtures and inspect the diff for unrelated template
   changes.
5. Roll back by restoring the previous dependency and renderer call boundary if
   compatibility or security validation fails before release.
