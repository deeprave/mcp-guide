## Context

When a tool is called with no project bound to the session, `_check_project_bound()` in
`core/tool_decorator.py` returns `RESULT_NO_PROJECT.to_json_str()` — a static constant
assembled from `INSTRUCTION_NO_PROJECT`, a hardcoded string in `result_constants.py`.

That string tells the agent to call `set_project` with its project directory path, but
gives no guidance on *which* path to send. Agents running inside isolated subdirectories
(e.g. Claude Code git worktrees at `.claude/worktrees/<name>`) will send their CWD, which
is a subdirectory of the real project root. The server hashes that path, produces the wrong
project identity, and all subsequent operations reference the wrong project.

The fix is to replace the static string with a rendered mustache template
(`_system/_project-root.mustache`) that gives the agent conditional, actionable
instructions for determining the correct project root — without the server ever needing to
touch the client filesystem.

**Constraints:**
- The MCP server has no direct filesystem access; all discovery must be agent-side.
- The template must render correctly with no bound project (no `project.*`, no project-
  specific `flags.*`, no `workflow.*`, no `client_working_dir`).
- The change must not alter any behavior for the already-bound project path.
- Agent info (`agent.is_<name>`) and client info (`client.*`) must be available so the
  template can conditionally branch on agent/OS type.

---

## Goals / Non-Goals

**Goals:**
- Replace `INSTRUCTION_NO_PROJECT` static string with a rendered template.
- Ensure `get_template_contexts()` renders a safe, minimal context when no project is bound
  (current behaviour — already graceful — must be explicitly verified and locked in by tests).
- Create `src/mcp_guide/templates/_system/_project-root.mustache` with agent-conditional
  instructions covering: git worktree detection, non-git fallback, and the path-relativity
  contract.
- Ensure `feature_flags` (global flags) remain available in the unbound context; project-
  specific flags return empty, merged `flags` contains only global flags.

**Non-Goals:**
- Server-side project root detection (the server never touches the filesystem).
- Any change to what happens after `set_project` is called (out of scope).
- Supporting VCS systems other than git in the template (non-git projects fall back to CWD,
  which is correct and sufficient).
- Changing how roots-based project binding works at handshake time.

---

## Decisions

### 1. `RESULT_NO_PROJECT` refactored into an async factory `make_no_project_result(ctx)`

**Decision:** `RESULT_NO_PROJECT` (static constant) is retained as a fallback value.
A new async factory `make_no_project_result(ctx)` is added in `result_constants.py`
that renders the `_project-root` template when a session is available, and falls back
to the static `RESULT_NO_PROJECT` when it cannot. All call sites that currently return
`RESULT_NO_PROJECT.to_json_str()` in the unbound-project path switch to
`(await make_no_project_result(ctx)).to_json_str()`. `_check_project_bound()` itself
becomes a thin delegator and stays simple.

**Rationale:** Centralising the rendering logic in the factory means:
- `_check_project_bound()` remains a simple two-branch function (bound / unbound).
- The fallback chain (render → static) lives in one place and is independently testable.
- Any future call site that needs to produce a no-project result gets the same behaviour
  without duplicating the rendering logic.

The static `RESULT_NO_PROJECT` constant is retained (not removed) because the factory
uses it as its own fallback when no session exists or rendering fails.

**Alternatives considered:**
- Render directly in `_check_project_bound()` — works but scatters the rendering/fallback
  logic across the tool decorator rather than owning it in `result_constants.py`.
- Render at module init time in `result_constants.py` — impossible; module initialisation
  is synchronous.
- Make `RESULT_NO_PROJECT` a coroutine — would break all existing call sites.

### 2. Re-use the existing `render_content("_project-root", "_system")` path

**Decision:** Use the existing `render_content(pattern, category_dir, extra_context)`
function from `rendering.py`. This is the same path used by `_update.mustache`,
`_missing_policy.md.mustache`, and `_startup.mustache`.

**Rationale:** All `_system/` templates already render without a bound project:
`_build_project_context()` gracefully returns empty defaults when `session.get_project()`
fails. No new rendering mode is required; the existing pipeline already handles this.
The only required change is confirming this is tested and not accidentally broken by future
refactors — enforced by adding an explicit test.

**Alternatives considered:**
- A separate "minimal context" rendering function — unnecessary complexity.
- Embedding agent instructions directly in Python as a multi-line string — defeats the
  purpose of the template system and makes agent-specific branching unreadable.

### 3. Git worktree detection via `git rev-parse --git-common-dir`

**Decision:** The template instructs the agent to run `git rev-parse --git-common-dir`
(which succeeds in both a main worktree and any linked worktree) and derive the main
repository root from its output, then fall back to CWD if git is not available or the
project is not git-controlled.

**Rationale:** `--git-common-dir` returns the shared `.git` directory path regardless of
whether the agent is in a linked worktree or the main worktree:
- Main worktree: returns `<root>/.git`
- Linked worktree: returns `<main-repo>/.git` (not the worktree's `.git` file)

Stripping the trailing `/.git` gives the main repository root in both cases. This is
VCS-agnostic at the server level — git is only invoked by the *agent*, which always has
local tool access.

The template does NOT use `.guide.yaml` or any mcp-guide-specific file as a marker,
because that file may not exist yet, may have a different name, or may exist at a
different level.

**Alternatives considered:**
- `git rev-parse --show-toplevel` — works in main worktree but returns the *worktree*
  root in a linked worktree, not the main repo root.
- Walking up looking for `.guide.yaml` — fragile: file may not exist, may be renamed,
  may exist at wrong level.
- Relying on MCP roots from handshake — correct when available, but this code path is
  only reached when roots were not provided.

### 4. `feature_flags` available in unbound context; project `flags` returns global-only

**Decision:** No code change required. `resolve_all_flags()` already returns global
(feature) flags only when no project is bound — project flags default to `{}`. The
template context's `feature_flags` key already contains global-only flags; `flags`
contains the merged set (global-only when no project). This existing behaviour is
documented and tested, not changed.

---

## Risks / Trade-offs

- **Rendering failure in error path** → If `render_content` itself fails (e.g. template
  missing, rendering exception), `_check_project_bound()` must catch and fall back to
  `RESULT_NO_PROJECT` static string rather than propagating the error. Mitigation: wrap
  in try/except; log warning; use static fallback.

- **Session available but agent info not yet populated** → If `send_working_directory`
  or similar is called before `client-context-setup` has run, `agent.*` and `client.*`
  will be empty. The template must use `{{#agent.is_claude}}` guards rather than assuming
  agent info is present. Mitigation: all template conditionals are optional — unguarded
  text is shown to all agents as a safe default.

- **No session at all (ValueError)** → Static fallback is used. The instruction is less
  helpful, but this is an edge case (no session means no MCP connection context at all).

---

## Migration Plan

1. Add `_project-root.mustache` template — inert until wired in.
2. Add async factory `make_no_project_result(ctx)` in `result_constants.py`; retain
   `RESULT_NO_PROJECT` static constant as the factory's internal fallback.
3. Update `_check_project_bound()` in `core/tool_decorator.py` to call the factory
   instead of referencing the static constant directly on the unbound path.
4. Verify unbound rendering pipeline; add tests.
5. No migration needed for deployed projects — change is transparent to callers.
