## 0. Vulture config cleanup

- [x] 0.1 Create `vulture_whitelist.py` with all `ignore_names` entries (with explanatory comments)
- [x] 0.2 Remove `ignore_names` from `pyproject.toml [tool.vulture]`
- [x] 0.3 Update pre-commit hook args to `['src', 'vulture_whitelist.py']`
- [x] 0.4 Verify `uv run vulture src vulture_whitelist.py` produces same output as before

## 1. Analyse and remove dead code clusters

Each task: remove dead code, remove/update tests that exclusively cover it, then verify ruff + ty + pytest + vulture.

Priority order: largest clusters first, then scattered items.

- [x] 1.1 `workflow/context.py` - WorkflowContextCache (160 lines)
- [x] 1.2 `render/context.py` - 5 dead functions (105 lines)
- [x] 1.3 `render/partials.py` - `resolve_partial_paths()` (62 lines)
- [x] 1.4 `filesystem/security.py` - SecurityPolicy class (62 lines)
- [x] 1.5 `core/mcp_log.py` - 3 logging functions (64 lines)
- [x] 1.6 `startup.py` - `handle_project_load()` — entire file deleted
- [x] 1.7 `render/renderer.py` - 2 dead functions (54 lines)
- [x] 1.8 `render/frontmatter.py` - 3 dead functions (42 lines)
- [x] 1.9 `openspec/task.py` - 4 dead methods (54 lines)
- [x] 1.10 `session.py` - 5 dead methods removed; `remove_current_session` whitelisted
- [x] 1.11 `server.py` - `initialize_task_manager` whitelisted (nested @mcp.on_init callback)
- [x] 1.12 Remaining scattered dead code
  - `content/gathering.py` `render_fileinfos()`
  - `content/utils.py` `read_file_contents()`
  - `render/renderer.py` `_build_transient_context()`
  - `utils/project_hash.py` `verify_project_hash()`
  - `task_manager/manager.py` `clear_cached_data()`
  - `session.py` `Session._state` attribute
  - `tools/tool_category.py` — 5 old wrapper functions removed
  - `tools/tool_collection.py` — 5 old wrapper functions removed
  - `tools/tool_feature_flags.py` — 2 old wrapper functions removed
  - `models/project.py` — `update_category`, `update_collection` removed
- [x] 1.13 Dead variables
  - `workflow/schema.py:13` `plan` — Pydantic model field, whitelisted as false positive
- [x] 1.14 Run vulture to confirm reduction — **0 items remaining**
