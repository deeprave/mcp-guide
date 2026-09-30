## 1. Shared elicitation model and continuation

- [x] 1.1 Move the existing skill-named elicitation parser and resolver to an entrypoint-neutral module, preserving the current primitive schema, URI keyword precedence, defaults, render fallback, explicit-decline, modern input-required, and legacy sequential contracts; verify existing skill resource regressions still pass
- [x] 1.2 Extend the current single-field string-equality `when` handling to validated multi-condition primitive equality-membership semantics, effective-form collision diagnostics, and condition-order tests covering applicable, skipped, and unresolved branches
- [x] 1.3 Implement integrity-protected modern-MCP continuation state for accepted values and completed forms, bound to the original interactive request; verify a branch can request a follow-up form without losing the first accepted value
- [x] 1.4 Preserve the compatible legacy sequential elicitation path and explicit non-eliciting-client guidance; verify both paths collect only currently applicable forms
- [x] 1.5 Verify shared modern and legacy skill flows retain their existing accepted-value, cancellation, default, fallback, and conditional-follow-up behaviour after neutralisation

## 2. Composed frontmatter properties

- [x] 2.1 Add a composable `DocumentElicitation` property to the document-property model and combine parent and eligible partial declarations with source-aware duplicate diagnostics; verify a partial contributes a distinct form to a parent entrypoint
- [x] 2.2 Extend the declared frontmatter partial path to process property-only partials without interpolating their bodies, retaining existing containment and `requires-*` behaviour; verify excluded partials do not contribute forms and listed property-only partials do
- [x] 2.3 Make interactive preflight collect effective elicitation properties before rendering a command or skill body; verify an inline partial must be explicitly listed to contribute pre-render input properties

## 3. Command and skill dispatch

- [x] 3.1 Route native command resources and the read_resource command surface through the shared pre-render elicitation resolver, preserving command URI path, positional arguments, keywords, and native input-required results; verify a command’s accepted response renders with merged kwargs
- [x] 3.2 Route underscore-prefixed Guide prompt commands through the same interaction contract without bypassing existing project binding or command argument handling; verify prompt, native resource, and read_resource results agree
- [x] 3.3 Migrate skill entrypoint handling to the neutral composed-property resolver; verify current skill forms, URI-supplied values, and conditional follow-up forms remain compatible

## 4. Documentation and verification

- [x] 4.1 Update developer skill, command, and template authoring documentation with shared forms, `when` branching, partial composition, continuation semantics, and the non-interactive document boundary; verify a strict documentation build succeeds
- [x] 4.2 Add focused behavioural coverage using controlled fixtures for command, skill, conditional, and property-only-partial flows without asserting shipped template wording; verify Ruff, Ty, strict OpenSpec validation, and the full foreground pytest suite pass

## 5. Review corrections

- [x] 5.1 Bind modern continuations to command positional arguments and requested forms; validate and normalise declared URI values; preserve URI precedence through cancellation; re-evaluate defaults and conditional forms; and retain nullable legacy optional primitives.
- [x] 5.2 Preserve MCP context through every prompt command route, resolve help before elicitation, provide entrypoint-neutral failures, and retain structured skill preflight failures.
- [x] 5.3 Render relevant frontmatter before preflight and delivery, carry property-only delivery properties without emitting bodies, and retain a typed, documented lazy renderer export.
- [x] 5.4 Run the final configured source checks, strict OpenSpec validation, documentation build, and complete foreground test suite.
- [x] 5.5 Apply accepted post-review corrections: retain explicit property-only cache policies, reconcile the defaulted-form contract, validate numeric constraints and overflow, preserve combined diagnostics and rendered parent variables during partial preflight, restrict public elicitation template context, and exercise registered modern prompt transport.
- [x] 5.6 Apply the latest accepted review corrections: use resolved parent frontmatter consistently through preflight and delivery, filter implicit cache defaults before delivery-property composition, and reject enum values with an incompatible primitive type.
- [x] 5.7 Apply the final review-triage corrections: retain tolerant logged listed-partial loading; selectively render interactive frontmatter without changing ordinary rendering; unify raw file reads; normalise numeric conditional semantics; strengthen conditional, capability, legacy-model, composition-diagnostic, and source-label behaviour; and verify commands and skills through behavioural fixtures.
