## 1. Recommendation rendering

- [x] 1.1 Add the common `recommend` template helper for `skill:`, `command:`, `content:`, and `tool:` references, defaulting unprefixed values to content; append fluent references and compact JSON footnotes during document rendering.
- [x] 1.2 Keep recommendation state inside rendering only. Do not add it to `RenderedContent`, Result, queues, listeners, or MCP responses. Preserve the complete render context when loading requirement-gated partials.

## 2. Skills

- [x] 2.1 Add contextual `recommend` use to an action-boundary skill template using the explicit `skill:` form.
- [x] 2.2 Add the project-dependent `{{tool_prefix}}use_skill` tool through `@toolfunc`. Accept an exact plain skill name with optional `$`, parse its `args` with the shared command parser (skill name at argv[0]), and render only its `SKILL.md` entrypoint.

## 3. Documentation and validation

- [x] 3.1 Update developer and skill-author guidance for typed recommendation forms.
- [x] 3.2 Run focused pytest coverage, Ruff check and format, strict OpenSpec validation for `add-recommend-items`, and `git diff --check`; the full suite passed (1946 tests).
