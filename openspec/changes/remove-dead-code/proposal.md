# Change: Remove dead and unreachable code

## Why
Vulture analysis identified ~942 lines (4.7% of codebase) of dead code across 22 files.
This increases maintenance burden, confuses contributors, and inflates test coverage gaps.

## What Changes
- Remove dead functions, methods, classes, and variables that are never called from production code
- Remove modules that exist only as test fixtures for unused functionality
- Fix duplicate `break` bug in `render/context.py`
- Prioritised by largest clusters first for maximum impact per task

## Impact
- Affected specs: session-management, workflow-context, template-context, logging, filesystem-security, template-rendering, mcp-server
- Affected code: 22 files across render/, workflow/, session.py, core/, openspec/, server.py, and others
- No breaking changes - all removed code is unreachable from production paths
- Tests that exercise dead-code-only modules may need removal

## Analysis Notes (2026-03-19)

Vulture currently reports zero issues at 80% confidence (the pre-commit threshold).
All dead code items appear only at 60% confidence — vulture's lowest tier.
The 80% threshold was masking them; the fix is to lower `min_confidence` to 60 and
add `ignore_decorators`/`ignore_names` entries for known false positives.

### False positives identified at 60% confidence

These must be whitelisted before lowering the threshold:

**Decorator-registered (add to `ignore_decorators`):**
- `@resourcefunc` — `guide_resource` in `resources.py`
- `@promptfunc` — prompt functions
- `@task_init` — `ClientContextTask`, `RetryTask`, `McpUpdateTask`, `WorkflowMonitorTask`, `WorkflowMonitorTask`, `OpenSpecTask`

**Framework/runtime attributes (add to `ignore_names`):**
- `model_config` — Pydantic ConfigDict (×3 files)
- `_flag_checked`, `_cached_content`, `_cached_mtime`, `_cached_context`, `_instruction_id` — instance attributes set at runtime
- `pygments_available`, `highlighter` — runtime-set attributes
- `original_event_types`, `queued_at`, `cached_at`, `access_count`, `from_value` — dataclass fields
- `TRACE`, `flags_list` — used within same file/scope (vulture false positive)
- `YamlValue` — type alias used in annotations

**API surface / interface methods (add to `ignore_names` or whitelist):**
- `send`, `receive` — abstract transport interface methods
- `is_failure` — Result type API
- `add_callback`, `unregister`, `cleanup_stopped`, `get_global_registry` — watcher/registry API
- `get_stats`, `get_violation_count` — diagnostic API
- `get_content` on `FileInfo` — likely used dynamically
- `is_timer_event` — utility predicate
- `LazyPath` — utility class

**Test/registry utilities (used only in tests — keep or remove with tests):**
- `enable_test_mode`, `disable_test_mode`, `clear_tool_registry`, `get_tool_registration`
- `clear_prompt_registry`, `clear_resource_registry`
- `_reset_for_testing`

**Tool functions (already covered by `@toolfunc` ignore but slip through at 60%):**
- `category_list/add/remove/change/update`, `collection_*`, `get_project_flag`, `get_feature_flag`
- `send_found_files`, `set_filesystem_trust_mode`

### Confirmed dead code (genuine removal candidates)

| Item | File | Notes |
|---|---|---|
| `WorkflowContextCache` | `workflow/context.py` | Only used in tests |
| `SecurityPolicy` | `filesystem/security.py` | Superseded by `ReadWriteSecurityPolicy` |
| `save_logging_config`, `restore_logging_config`, `configure` | `core/mcp_log.py` | Never called |
| `handle_project_load` | `startup.py` | Never called |
| `resolve_partial_paths` | `render/partials.py` | Never called |
| `get_partial_name`, `render_template_with_context_chain` | `render/renderer.py` | Never called |
| `soft_delete`, `hard_delete` | `render/context.py` | Never called |
| `build_template_context`, `add_file_context`, `get_user_context` | `render/context.py` | Never imported |
| `get_frontmatter_instruction`, `get_frontmatter_description`, `validate_content_type` | `render/frontmatter.py` | Never called |
| `_build_collection_context` | `render/cache.py` | Never called |
| `is_project_enabled`, `_format_status_response`, `_format_changes_list_response`, `_format_show_response` | `openspec/task.py` | Never called |
| `initialize_task_manager` | `server.py` | Inner function, never called |
| `remove_listener`, `clear_listeners`, `has_current_session`, `is_watching_config`, `get_state` | `session.py` | Never called |
| `remove_current_session` | `session.py` | Never called |
| `update_category`, `update_collection` | `models/project.py` | Never called |
| `category_list`, `category_add`, `category_remove`, `category_change`, `category_update` | `tools/tool_category.py` | Not registered as MCP tools, never called |
| `collection_list`, `collection_add`, `collection_remove`, `collection_change`, `collection_update` | `tools/tool_collection.py` | Not registered as MCP tools, never called |
| `get_project_flag`, `get_feature_flag` | `tools/tool_feature_flags.py` | Not registered as MCP tools, never called |
| `render_fileinfos` | `content/gathering.py` | Never called |
| `read_file_contents` | `content/utils.py` | Never called |
| `parse_guide_uri` (+ `GuideUri`) | `uri_parser.py` | Never called |
| `get_target_project` | `feature_flags/resolution.py` | Never called |
| `install_directory` | `installer/core.py` | Never called |
| `validate_workflow_file_path`, `validate_startup_expression` | `workflow/flags.py` | Never called |
| `validate_category_exists` | `validation.py` | Never called |
| `verify_project_hash` | `utils/project_hash.py` | Never called |
| `clear_cached_data` | `task_manager/manager.py` | Never called |
| `_reset_overrides` | `config_paths.py` | Never called |
| `is_valid_partial` | `discovery/patterns.py` | Never called |
