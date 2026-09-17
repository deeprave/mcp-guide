## 1. Shared elicitation model and continuation

- [ ] 1.1 Move the existing skill-named elicitation parser and resolver to an entrypoint-neutral module, preserving the current primitive schema and URI keyword contract; verify existing skill resource regressions still pass
- [ ] 1.2 Add validated `when` conditions with primitive equality-membership semantics, effective-form collision diagnostics, and condition-order tests covering applicable, skipped, and unresolved branches
- [ ] 1.3 Implement integrity-protected modern-MCP continuation state for accepted values and completed forms, bound to the original interactive request; verify a branch can request a follow-up form without losing the first accepted value
- [ ] 1.4 Preserve the compatible legacy sequential elicitation path and explicit non-eliciting-client guidance; verify both paths collect only currently applicable forms

## 2. Composed frontmatter properties

- [ ] 2.1 Add a composable `DocumentElicitation` property to the document-property model and combine parent and eligible partial declarations with source-aware duplicate diagnostics; verify a partial contributes a distinct form to a parent entrypoint
- [ ] 2.2 Extend the declared frontmatter partial path to process property-only partials without interpolating their bodies, retaining existing containment and `requires-*` behaviour; verify excluded partials do not contribute forms and listed property-only partials do
- [ ] 2.3 Make interactive preflight collect effective elicitation properties before rendering a command or skill body; verify an inline partial must be explicitly listed to contribute pre-render input properties

## 3. Command and skill dispatch

- [ ] 3.1 Route native command resources and the read_resource command surface through the shared pre-render elicitation resolver, preserving command URI path, positional arguments, keywords, and native input-required results; verify a command’s accepted response renders with merged kwargs
- [ ] 3.2 Route underscore-prefixed Guide prompt commands through the same interaction contract without bypassing existing project binding or command argument handling; verify prompt, native resource, and read_resource results agree
- [ ] 3.3 Migrate skill entrypoint handling to the neutral composed-property resolver; verify current skill forms, URI-supplied values, and conditional follow-up forms remain compatible

## 4. Documentation and verification

- [ ] 4.1 Update developer skill, command, and template authoring documentation with shared forms, `when` branching, partial composition, continuation semantics, and the non-interactive document boundary; verify a strict documentation build succeeds
- [ ] 4.2 Add focused behavioural coverage using controlled fixtures for command, skill, conditional, and property-only-partial flows without asserting shipped template wording; verify Ruff, Ty, strict OpenSpec validation, and the full foreground pytest suite pass
