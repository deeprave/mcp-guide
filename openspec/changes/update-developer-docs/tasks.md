## 1. Template variable reference

- [ ] 1.1 Create `docs/developer/template-variables.md` enumerating every variable produced by `TemplateContextCache._build_system_context`, `_build_client_context`, `_build_agent_context`, `_build_project_context`, and `_build_openspec_context` (`src/mcp_guide/render/cache.py`), plus `get_transient_context()`. For each variable, state its layer, whether it's present with no bound session, and a one-line description. Verify completion by cross-checking every variable name in the doc against the current source of each `_build_*_context` method, confirming none are missing or invented.
- [ ] 1.2 Document category-specific and command-specific extra-context injection: `_build_category_context`'s `category.*`, policy pre-rendering's `policy_topic`/`policy_category`/`policy_path`, and the general `extra_context` mechanism individual templates can receive from their calling code (with `_project-root`'s `tool_prefix` and `_filesystem-probe`'s `path` as concrete examples). Verify completion by the doc distinguishing this from the always-available layered variables in task 1.1, with at least two concrete template examples cited.
- [ ] 1.3 Cross-reference the new file from `docs/developer/template-rendering.md`. Verify completion by confirming the link resolves and reads naturally in context.

## 2. Disposition documentation (current state only)

- [ ] 2.1 Add a section to `docs/developer/template-rendering.md` documenting `Result.disposition` as a field distinct from template frontmatter `type:`, describing their relationship (frontmatter `type:` is how a template declares its disposition; `disposition` is the resolved value on the response `Result`). Verify completion by the section accurately reflecting the current `src/mcp_guide/core/result.py` and `src/mcp_guide/render/content.py` (`RenderedContent.disposition`) behavior at time of writing.
- [ ] 2.2 Note explicitly in that section that the full disposition vocabulary (including `agent/error`, `user/error`, and the disposition-guide teaching template) is landing via the separate `cooperative-result-disposition` change, with a pointer to it, rather than documenting vocabulary that doesn't exist yet. Verify completion by the note being accurate and not overstating what's implemented at time of writing.

## 3. Documents, commands, skills, and resources relationship

- [ ] 3.1 Write or extend a section (in `docs/developer/command-authoring.md` or a new file, per design.md's judgment during writing) describing how documents, commands, skills, and the `guide://` resource scheme relate to each other — how a command renders content, how a skill entrypoint's frontmatter relates to ordinary document frontmatter, and how resources surface both. Verify completion by the section covering all four concepts and their relationships, cross-referencing rather than duplicating existing per-topic docs (`skill-authoring.md`, `template-rendering.md`).

## 4. Consistency pass

- [ ] 4.1 Confirm `docs/developer/skill-authoring.md`'s existing frontmatter cross-reference still points to accurate content after tasks 1-3 (update the cross-reference target if content moved). Verify completion by reading the cross-reference in context and confirming it resolves correctly.
- [ ] 4.2 Re-read all touched/created files standalone to confirm they read coherently and no content was duplicated across files where a cross-reference would serve better. Verify completion by a brief per-file note confirming this check was done.
