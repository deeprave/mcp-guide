## Why

Guide's developer documentation under `docs/developer/` covers mustache/frontmatter basics, command authoring, and skill authoring, but has real gaps: it never documents the `Result.disposition` field (distinct from template frontmatter `type:`) or the disposition vocabulary the `cooperative-result-disposition` change is introducing; it has no complete reference of which template variables are available, in what layer, with or without a bound session; and it doesn't describe how documents, commands, skills, and resources relate to each other as a whole system. Contributors and agents authoring templates today have to read source code (`render/cache.py`'s context-building functions, `render/frontmatter.py`'s type/instruction resolution) to answer questions the docs should answer directly.

## What Changes

- Add a `disposition` section to the developer docs distinguishing it from template frontmatter `type:` (the two are related but not identical: `type:` is how a template declares its disposition; `disposition` is the resolved value on the `Result` the client receives), covering the disposition vocabulary defined by `cooperative-result-disposition` (three content dispositions, two error dispositions) once that change has landed.
- Document the `_system/_disposition-guide.mustache` teaching template and its once-per-session delivery mechanism, once `cooperative-result-disposition` has implemented it — this documentation task is sequenced after that change's implementation, not before.
- Produce a complete template variable reference: every variable available in each context layer (`system`, `agent`, `client`, `project`, `openspec`, plus transient timestamp variables) as built by `TemplateContextCache`'s `_build_*_context` methods, explicitly marking which variables are present with no bound session versus which require one, and which category/command-specific mechanisms can inject additional variables into specific templates (e.g. policy pre-rendering's `policy_topic`/`policy_category`/`policy_path`, category-specific context).
- Document the relationship between documents served by Guide, commands, skills, and resources — how a skill entrypoint's frontmatter relates to ordinary document frontmatter (already partially covered in `skill-authoring.md` via cross-reference), how commands render content, and how the `guide://` resource scheme surfaces all of the above.
- Preserve the existing cross-referencing structure (`skill-authoring.md` pointing to `template-rendering.md`'s frontmatter fields rather than duplicating them) rather than consolidating everything into one large document.

This is a documentation-only change: no source code, no observable system behavior, and no spec-level requirement is added, changed, or removed. `skip_specs: true` is set accordingly.

## Capabilities

### New Capabilities
(none — `skip_specs: true`, no spec-level behavior changes)

### Modified Capabilities
(none — `skip_specs: true`, no spec-level behavior changes)

## Impact

- `docs/developer/template-rendering.md` — add `disposition` field documentation, expand the template variable reference.
- `docs/developer/skill-authoring.md` — update its frontmatter cross-reference if the shared frontmatter reference material moves or is restructured; no content duplication introduced.
- `docs/developer/command-authoring.md` — document the document/command/skill/resource relationship as it pertains to command authoring.
- Possibly a new `docs/developer/` file for the template variable reference and the documents/commands/skills/resources relationship overview, if that content doesn't fit naturally into the existing files (decided during design).
- No changes to `src/mcp_guide/*` or any OpenSpec capability spec.
