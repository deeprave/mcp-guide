## 1. Worktree watchdog

- [x] 1.1 Extend `protect_production_files` to watch the repository root as well as existing production XDG paths, counting only events after the fixture starts, and verify `tests/test_file_protection.py` still covers the XDG guard.
- [x] 1.2 Filter worktree events with gitignore semantics (root and nested `.gitignore`) so ignored paths do not abort the session, and verify a test can write under a gitignored path without `pytest.exit`.
- [x] 1.3 Abort the test session when a non-gitignored worktree path is created or modified, naming that path, and verify a focused test that writes `tests/fixtures/sentinel` (or equivalent) triggers the guard.
- [x] 1.4 Move `tests/test_render_template.py` cwd-relative writes under `tmp_path` and verify those tests pass with the worktree guard enabled.

## 2. Absolute docroot defaults

- [x] 2.1 When `docroot` is missing, blank, or not a string, persist `config_file.parent.resolve() / "docs"` and verify the written value is absolute and is not CWD-relative.
- [x] 2.2 Ensure filling a missing `docroot` key does not unpack templates, and verify no `.original.zip` / template tree appears beside the config file in that case.
- [x] 2.3 Make first-run `install_and_create_config` store resolved absolute config and docroot paths, and verify a relative `config_dir` still writes absolute `docroot` in `config.yaml`.

## 3. Runtime-owned ConfigManager, flags, and docroot

- [x] 3.1 Make `GuideRuntime` construct `ConfigManager` from `config_dir`/`docroot` and verify `server.py` no longer imports `ConfigManager`.
- [x] 3.2 Move the `ConfigManager` class out of `session.py` so that module does not import it, type `Session._config()` via the runtime, and verify Session project CRUD tests still pass.
- [x] 3.3 Replace test `ConfigManager(...)` construction with `GuideRuntime` / `create_test_runtime(config_dir)`, and verify `ConfigManager` is imported only from `GuideRuntime`.
- [x] 3.4 Add `GuideRuntime` global feature-flag list/get/set/remove that defer to `ConfigManager`, and verify unit tests exercise those methods without a Session.
- [x] 3.5 Point the global `FeatureFlags` handler at `GuideRuntime` (not Session or ConfigManager) and verify `list`/`set`/`remove` tests pass through the runtime.
- [x] 3.6 Replace `session.feature_flags()` and Session global-flag methods with runtime access, keep `project_flags` on Session, and verify feature-flag tool tests still pass.
- [x] 3.7 Replace `session.get_docroot()` call sites with `GuideRuntime.get_docroot()`, remove Session ownership of process docroot if call sites are gone, and verify content/render/update tests still resolve docroot.

## 4. Verification

- [x] 4.1 Run `uv run pytest tests/test_file_protection.py tests/test_render_template.py tests/integration/test_config_docroot.py tests/unit/test_mcp_guide/tools/test_tool_feature_flags.py -q --tb=line` and verify it passes.
- [x] 4.2 Run `openspec validate protect-worktree-for-tests --strict` and verify it passes.
