## Why

A first-run Guide install wrote a full template docroot into this repository
(`tests/fixtures/docs` plus a sibling `config.yaml`) because configuration
resolution accepted a relative config directory and, when `docroot` was missing,
defaulted beside that path. The existing `protect_production_files` watchdog
cannot detect that class of damage: it only watches pre-existing production XDG
trees, not the worktree. Tests that appear isolated can therefore plant
installer artefacts in git-tracked paths without failing.

## What Changes

- Extend the pytest production-file watchdog so it also watches the repository
  worktree during a test session and aborts if a test writes a non-gitignored
  path.
- Ignore changes that match `.gitignore` (and nested gitignore rules), so
  expected artefacts such as `.venv`, `__pycache__`, and coverage output do not
  trip the watchdog.
- Keep watching the captured production XDG config/docroot paths as today.
- Resolve a missing or blank `docroot` in `config.yaml` to an absolute path
  beside the config file. Never persist a CWD-relative docroot, and never unpack
  templates into the worktree as a side effect of filling that key.
- Access process docroot only through `GuideRuntime`. Callers must not treat
  `Session` as the owner of docroot.
- Move **global** feature-flag list/get/set/remove onto `GuideRuntime`, which
  defers persistence to `ConfigManager`. The global `FeatureFlags` handler must
  not take `ConfigManager` or `Session`.
- Leave **project** feature flags on the bound Session's project configuration.
  Those flags are per-interaction project state, not process globals.
- `GuideRuntime` SHALL construct its own `ConfigManager` from the config
  directory and docroot it already has. `server.py` SHALL NOT import or
  construct `ConfigManager`; it only constructs `GuideRuntime`.
- `Session._config()` remains the in-Session accessor for project CRUD, clone
  lookup, and registration, but it SHALL obtain the service from
  `GuideRuntime`. The Session module SHALL NOT import `ConfigManager`.
- Production code SHALL import and instantiate `ConfigManager` in exactly one
  place: `GuideRuntime`. Tests construct a runtime (or a test helper that
  does), not a bare `ConfigManager`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `test-quality`: Test runs SHALL fail if they modify a non-gitignored worktree
  path, while still protecting production XDG paths.
- `config-manager`: Missing or blank `docroot` SHALL resolve to an absolute
  default beside the config file; relative CWD defaults and worktree template
  dumps SHALL NOT occur. `GuideRuntime` is the only production constructor of
  `ConfigManager`.
- `feature-flags`: Global feature-flag operations SHALL be owned by
  `GuideRuntime` (deferring to `ConfigManager`), not `Session`.
- `session-management`: `Session` SHALL NOT own process docroot or global
  feature flags. Project flags remain Session/project-scoped. `Session._config()`
  SHALL reach configuration only through `GuideRuntime`.

## Impact

- Affected code: `tests/conftest.py`, `tests/test_file_protection.py`,
  `src/mcp_guide/runtime.py`, `src/mcp_guide/server.py`,
  `src/mcp_guide/session.py` (move or hide `ConfigManager`; Session facades),
  `src/mcp_guide/feature_flags/feature_flags.py`,
  `src/mcp_guide/installer/integration.py`, callers of `session.get_docroot()`
  and `session.feature_flags()`, `tests/helpers.py`, and every test that
  constructs `ConfigManager` directly.
- Public MCP tool names and schemas stay the same. Internal ownership of
  docroot, global flags, and `ConfigManager` construction changes.
- Watchdog implementation will need a gitignore-aware path filter (likely
  `pathspec` against the root and nested `.gitignore` files, or `git
  check-ignore`). That filter must not itself write to the worktree.
- Handler-signature migration remains `use-request-context`. This change
  finishes ConfigManager construction/import encapsulation behind
  `GuideRuntime`.
