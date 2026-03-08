## 1. Analyse and remove dead code clusters

Priority order: largest clusters first, then scattered items.

- [ ] 1.1 `workflow/context.py` - WorkflowContextCache (160 lines)
  - Entire class only imported by tests
  - Analyse: is this a planned feature or abandoned code?
  - If dead: remove class, remove tests that only exercise it

- [ ] 1.2 `render/context.py` - 5 dead functions (105 lines)
  - `soft_delete()`, `hard_delete()` - never called (also fix duplicate `break` bug)
  - `build_template_context()`, `add_file_context()`, `get_user_context()` - never imported
  - Analyse: were these superseded by cache.py?

- [ ] 1.3 `render/partials.py` - `resolve_partial_paths()` (62 lines)
  - Never imported from production code
  - Analyse: superseded by different partial resolution?

- [ ] 1.4 `filesystem/security.py` - SecurityPolicy class (62 lines)
  - Only imported by tests; `read_write_security.py` exists with `ReadWriteSecurityPolicy`
  - Analyse: is this the predecessor? If so, remove class and its tests

- [ ] 1.5 `core/mcp_log.py` - 3 logging functions (64 lines)
  - `save_logging_config()`, `restore_logging_config()`, `configure()`
  - Analyse: leftover from earlier logging approach?

- [ ] 1.6 `startup.py` - `handle_project_load()` (41 lines)
  - Never imported
  - Analyse: was this replaced by session startup?

- [ ] 1.7 `render/renderer.py` - 2 dead functions (54 lines)
  - `get_partial_name()`, `render_template_with_context_chain()`
  - Analyse: superseded by template.py?

- [ ] 1.8 `render/frontmatter.py` - 3 dead functions (42 lines)
  - `get_frontmatter_instruction()`, `get_frontmatter_description()`, `validate_content_type()`

- [ ] 1.9 `openspec/task.py` - 4 dead methods (54 lines)
  - `is_project_enabled()`, `_format_status_response()`, `_format_changes_list_response()`, `_format_show_response()`

- [ ] 1.10 `session.py` - 6 dead methods (27 lines)
  - `remove_listener()`, `clear_listeners()`, `has_current_session()`, `is_watching_config()`, `get_state()`, `remove_current_session()`

- [ ] 1.11 `server.py` - 2 dead functions (13 lines)
  - `initialize_task_manager()`, `register_startup_listener()`

- [ ] 1.12 Remaining scattered dead code (73 lines)
  - `content/gathering.py` `render_fileinfos()` (35 lines)
  - `content/utils.py` `read_file_contents()` (18 lines)
  - `uri_parser.py` `GuideUri`, `parse_guide_uri()` (34 lines, test-only)
  - `feature_flags/resolution.py` `get_target_project()` (19 lines)
  - `installer/core.py` `install_directory()` (14 lines)
  - `workflow/flags.py` `validate_workflow_file_path()`, `validate_startup_expression()` (49 lines)
  - `render/cache.py` `_build_collection_context()` (24 lines)
  - `config_paths.py` `_reset_overrides()` (5 lines)
  - `discovery/patterns.py` `is_valid_partial()` (11 lines)
  - `guide.py` `set_instructions()` (7 lines)
  - `validation.py` `validate_category_exists()` (13 lines)
  - `utils/project_hash.py` `verify_project_hash()` (26 lines)
  - `task_manager/manager.py` `clear_cached_data()` (3 lines)
  - `types.py` `YamlValue` (1 line)

- [ ] 1.13 Dead variables
  - `core/mcp_log.py:15` `TRACE` alias
  - `render/cache.py:216` `flags_list`
  - `workflow/change_detection.py:25` `from_value`

- [ ] 1.14 Run vulture to confirm reduction, update analysis report
