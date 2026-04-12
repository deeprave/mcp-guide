## 1. Template

- [ ] 1.1 Create `src/mcp_guide/templates/_system/_project-root.mustache` with frontmatter (`type: agent/instruction`), git worktree detection instructions (`git rev-parse --git-common-dir` → strip `/.git`), non-git CWD fallback, path-relativity contract statement, and `set_project` call instruction
- [ ] 1.2 Add optional `{{#agent.is_claude}}` / `{{#agent.is_codex}}` conditional blocks where agent-specific phrasing improves clarity — ensure all conditionals degrade gracefully when agent info is absent
- [ ] 1.3 Verify template renders without error using `render_content("_project-root", "_system")` in an unbound session (manual smoke test or quick script)

## 2. Rendering pipeline — unbound session support

- [ ] 2.1 Review `render_content()` in `rendering.py` and confirm it does not raise when called with an unbound session (trace through `session.docroot`, `session.project_path`, and any other session attributes accessed before project context)
- [ ] 2.2 If any attribute access raises with an unbound session, add a guard or default — without changing behaviour for the bound-session path
- [ ] 2.3 Confirm `_build_project_context()` in `render/cache.py` already returns empty defaults for all project variables when `session.get_project()` raises; add a comment marking this as load-bearing behaviour if not already present

## 3. Async factory in `result_constants.py`

- [ ] 3.1 Add `async def make_no_project_result(ctx: Optional[Any] = None) -> "Result[Any]"` to `result_constants.py`
- [ ] 3.2 Factory body: attempt `get_session(ctx)` → render `_project-root` via `render_content` → construct `Result.failure(error_type=ERROR_NO_PROJECT, instruction=<rendered>)` and return it
- [ ] 3.3 On `ValueError` from `get_session` (no session), return `RESULT_NO_PROJECT` static fallback
- [ ] 3.4 Wrap `render_content` call in `try/except`; log a warning and return `RESULT_NO_PROJECT` on any rendering failure
- [ ] 3.5 Retain `INSTRUCTION_NO_PROJECT` and `RESULT_NO_PROJECT` as the factory's internal static fallback and do not remove them; if `INSTRUCTION_NO_PROJECT` wording changes intentionally, keep this task entry aligned with that updated text/behavior

## 4. Update `_check_project_bound()` in `core/tool_decorator.py`

- [ ] 4.1 Replace the `return RESULT_NO_PROJECT.to_json_str()` call on the unbound-project branch with `return (await make_no_project_result(ctx)).to_json_str()`
- [ ] 4.2 Retain the `except ValueError` path returning `RESULT_NO_PROJECT.to_json_str()` — the factory already handles this, but if the ValueError is raised before the factory is called, the static fallback is still correct
- [ ] 4.3 Confirm the bound-session path (`return None`) is entirely untouched

## 5. Tests

- [ ] 5.1 Add a test that renders `_project-root` with a mock unbound session and asserts the output contains the `git rev-parse --git-common-dir` instruction and the CWD fallback
- [ ] 5.2 Add a test that renders `_project-root` with a mock bound session and asserts the output is identical (template does not reference any project variables)
- [ ] 5.3 Add a test for `make_no_project_result(ctx)` with an unbound session: assert the returned `Result` instruction contains the rendered template content (not the static fallback string)
- [ ] 5.4 Add a test for `make_no_project_result(ctx)` where `render_content` raises: assert it returns `RESULT_NO_PROJECT` and logs a warning
- [ ] 5.5 Add a test for `make_no_project_result(ctx=None)` (no context / no session): assert it returns `RESULT_NO_PROJECT`
- [ ] 5.6 Add a test confirming `_check_project_bound()` with a bound session returns `None` and never calls `make_no_project_result`
