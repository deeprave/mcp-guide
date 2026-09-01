## Context

See proposal.md for motivation. Constraints that shape the approach:

- `protect_production_files` in `tests/conftest.py` already captures real XDG
  paths before pytest redirects `HOME` / `XDG_CONFIG_HOME`, then watches those
  paths only if they already exist. It never watches the repository.
- `ConfigManager.get_docroot` fills a missing `docroot` key with
  `get_default_docroot(config_dir)`, which is `Path(config_dir) / "docs"` and
  stays relative when `config_dir` is relative. First-run
  `install_and_create_config` writes `docroot: {docroot}` the same way and
  unpacks the packaged templates there.
- `Session.get_docroot` already delegates to `GuideRuntime.get_docroot`.
  Callers still go through Session. Global `FeatureFlags` wraps Session, which
  wraps `ConfigManager`.
- `Session._config()` remains the in-Session accessor, but it must ask
  `GuideRuntime` rather than importing `ConfigManager`. The class currently
  lives in `session.py` and is constructed in `server.py`, `tests/helpers.py`,
  and many tests.
- `use-request-context` already aims to keep `ConfigManager` private to
  `GuideRuntime`. This change now includes that construction/import boundary.

## Goals / Non-Goals

**Goals:**

- Fail a test session that writes a non-gitignored worktree path.
- Ignore gitignored writes without writing tracked files from the guard itself.
- Persist absolute docroot defaults; stop CWD-relative first-run dumps.
- Put process docroot and global feature flags on `GuideRuntime`.
- Keep project flags on the bound Session/project.
- Make `GuideRuntime` the only production importer and constructor of
  `ConfigManager`. `server.py` constructs `GuideRuntime` with a config
  directory; it does not know about `ConfigManager`.

**Non-Goals:**

- Migrating tool/prompt/resource handlers to `RequestContext` (that is
  `use-request-context`).
- Changing public MCP tool names or flag schemas.
- Watching production XDG paths that do not yet exist (creating them is still
  a separate production-path issue; this change's new coverage is the worktree).
- Removing `Session._config()` — it stays as a Session-private accessor that
  forwards to the runtime.

## Decisions

### 1. Worktree watchdog uses gitignore matching, not a hand-maintained allowlist

Watch the repository root recursively from the same session-scoped autouse
fixture that already watches XDG. Filter events with gitignore semantics
(root `.gitignore`, nested `.gitignore`, and standard git exclude rules).

Prefer `pathspec` against loaded gitignore files, or `git check-ignore --stdin`,
over a hardcoded list. `git check-ignore` is accurate but slower and requires a
git worktree; `pathspec` is fast and must replicate nested gitignore behaviour
closely enough that `.venv`, `__pycache__`, and coverage files stay silent.

The filter runs inside the handler. It MUST NOT create files in the worktree.

**Alternatives considered:** Watch only `src/` and `tests/` — too narrow; the
observed dump was `tests/fixtures/docs` and a template-tree `config.yaml`.
Abort on any worktree write including gitignored paths — too noisy for pytest
cache and bytecode.

### 2. Snapshot worktree mtimes at session start for the baseline

A recursive watchdog on a large tree is noisy (editor/OS events). Combine:

- Watcher events for creates/modifies/deletes under the repo root.
- Ignore events whose path is gitignored **or** whose path is outside the
  worktree (the XDG watches stay separate).
- Ignore the pytest session temp dir even if it were somehow nested (it is
  created under the system temp, not the repo).

Do not treat pre-existing dirty files as violations. Only events after the
fixture starts count.

### 3. Absolute docroot is `config_file.parent / "docs"` resolved

When filling a missing `docroot`, resolve `config_file.parent.resolve() / "docs"`
and persist that absolute string. First-run install must pass the same resolved
paths into `install_and_create_config`. Filling a missing key MUST NOT call
`install_templates`.

**Alternatives considered:** Refuse to start without an explicit docroot —
stricter, but breaks first-run. Keep relative paths but interpret them against
the config file — still easy to mis-read as CWD-relative, which is how
`tests/fixtures/docs` was persisted.

### 4. GuideRuntime constructs ConfigManager

`GuideRuntime.__init__` takes `config_dir` (and optional `docroot`), constructs
`ConfigManager` internally, and is the only production `import` of that class.
Move the class out of `session.py` into a module imported solely by
`runtime.py` (for example keep the implementation next to runtime, not next to
Session).

`server.py` already builds `GuideRuntime` for FastMCP lifespan. It stops
importing `ConfigManager` and passes `config.configdir` into `GuideRuntime`.
That is the sense in which the server need not know about the configuration
runtime: it is created inside `GuideRuntime`.

`Session._config()` calls `self._runtime.configuration_service()` (or equivalent)
and types it with a protocol defined without importing `ConfigManager`.
Project CRUD stays on Session through that accessor.

Tests use `create_test_runtime(config_dir)` / `GuideRuntime(..., config_dir=...)`.
Direct `ConfigManager(...)` in tests is removed.

**Alternatives considered:** Keep injecting `ConfigManager` for tests — that
is how the leak in `server.py` started. A protocol-shaped fake can still be
avoided because tests want a real config file.

### 5. Global FeatureFlags takes GuideRuntime

`GuideRuntime.feature_flags()` returns the existing handler type, constructed
with the runtime. The handler calls `GuideRuntime` methods that defer to
`ConfigManager`. Remove `Session.feature_flags()`, `get_feature_flags`,
`set_feature_flag`, and `remove_feature_flag` for **global** flags.

`ProjectFlags` stays on Session because it mutates the bound project via
`update_config`.

Callers that have a Session today (`session.feature_flags()`,
`session.get_docroot()`) switch to `session.runtime` / an explicit runtime
argument. Until `use-request-context` lands, Session may keep a thin
`get_docroot` that only forwards to `GuideRuntime`, but specs treat runtime as
the owner; the Session method is a compatibility shim to delete if call sites
are fully migrated in this change.

**Confirmation:** `Session._config()` is the right in-Session shape. After this
change it does not import `ConfigManager`. Remaining production `ConfigManager`
use is the constructor inside `GuideRuntime` only.

### 6. `test_render_template.py` cwd-relative fixture writes are in scope

Those tests write `Path("tests/fixtures/....mustache")` then unlink. After the
watchdog lands they MUST use `tmp_path` (or they will abort the suite). Treat
that as required cleanup in this change, not a later follow-up.

## Risks / Trade-offs

- [Watchdog false positives on gitignored files] → Use gitignore matching and
  add a regression that writes under a gitignored path without aborting.
- [Watchdog false positives on pre-existing dirty trees] → Count only events
  after fixture start.
- [macOS FSEvents teardown] → Keep `PollingObserver` on Darwin as today.
- [Session still talks to ConfigManager] → It talks to the runtime-owned
  service through `_config()`, without importing the class.
- [Overlap with `use-request-context`] → Limit this change to flags, docroot,
  and the watchdog; do not migrate handler signatures.

## Migration Plan

1. Land watchdog and gitignore filter with tests, then fix tests that write
   into `tests/fixtures/`.
2. Absolute docroot default and first-run install path resolution.
3. Move `ConfigManager` construction into `GuideRuntime`; stop `server.py` and
   tests importing the class.
4. Move global flag API onto `GuideRuntime` and update callers.
5. Remove Session global-flag methods once callers are gone.

Rollback is revert of the change; no persisted schema migration.

## Open Questions

None. Nested gitignore matching is an implementation choice under Decision 1
and does not change the spec.
