## 1. Recommendation rendering

- [ ] 1.1 Add the common `recommend` template helper and carry its ordered non-empty rendered recommendation items through `RenderedContent`; verify focused rendering tests cover invisible helper output, context interpolation, explicit Guide-skill item fields, ordering, and an empty recommendation.
- [ ] 1.2 Preserve recommendations when rendered content and partial contributions are assembled; verify a behaviour test observes recommendations from the complete rendered response without asserting shipped template prose.

## 2. Structured delivery

- [ ] 2.1 Extend Guide result and MCP response adaptation so recommendations are delivered as optional `mcp-guide.recommendations` metadata without changing existing instruction or cache metadata; verify tool, prompt, resource, and retained-client response behaviours.
- [ ] 2.2 Add a `requires-mcp-skills` startup partial that authors suggested Guide-skill recommendations, and deliver them as optional `suggested_guide_skills` startup metadata; verify the partial contributes only when the global experiment is enabled.
- [ ] 2.3 Add contextual `recommend` use to an appropriate action-boundary template. For a Guide skill, use the `Guide skill "<name>"` form, retain a fluent visible instruction, and use a footnote-style resource fallback where visible linking helps; verify client-driven recommendation behaviour rather than literal template text.

## 3. Documentation and validation

- [ ] 3.1 Document the `recommend` helper and structured recommendation metadata for template and client authors; verify the documentation examples match the declared metadata keys.
- [ ] 3.2 Run focused pytest coverage, Ruff check and format, strict OpenSpec validation for `add-recommend-items`, and `git diff --check`; record any full-suite result or environmental blocker.
