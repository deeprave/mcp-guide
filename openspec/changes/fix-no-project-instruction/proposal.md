## Why

When no project is bound to a session, the server returns a hardcoded string (`INSTRUCTION_NO_PROJECT`) instructing the agent to call `set_project` with its project root — but gives no guidance on how to determine which directory that is. Agents running inside isolated environments (Claude Code git worktrees, container mounts, etc.) will naively send their current working directory, which may be a subdirectory rather than the actual project root, causing the server to compute the wrong project hash and bind to the wrong project. The instruction needs to be a rendered template so it can include agent-aware, conditional guidance on project root resolution.

## What Changes

- **Remove** the hardcoded `INSTRUCTION_NO_PROJECT` string constant from `result_constants.py`
- **Add** `src/mcp_guide/templates/_system/_project-root.mustache` — a new template that instructs the agent how to determine and send the correct project root, with conditional logic based on agent/client context (e.g. git worktree detection for git-controlled projects, fallback to CWD otherwise)
- **Modify** `RESULT_NO_PROJECT` construction to render the `_project-root` template instead of using the static string
- **Modify** template rendering infrastructure to support rendering the `_project-root` template in an unbound session context — without requiring a bound project, resolved flags, or project-specific template variables
- **Ensure** client/agent info (sufficient for `agent.is_<name>` conditionals) is available during unbound rendering so the template can branch on agent type

## Capabilities

### New Capabilities

- `unbound-session-rendering`: Template rendering in an unbound (no active project) session context, with a minimal variable set (client info, agent info, tool prefix) sufficient for agent instruction templates

### Modified Capabilities

- `template-rendering`: Rendering pipeline must support a reduced context mode for unbound sessions, without raising errors on missing project variables
- `session-management`: `RESULT_NO_PROJECT` construction switches from a static string to a rendered template result
- `filesystem-interaction`: `_project-root` template instructs the agent on project root resolution — covering git worktree detection, non-git fallback, and the implication that all relative paths the MCP uses are relative to the provided root

## Impact

- `src/mcp_guide/result_constants.py` — `INSTRUCTION_NO_PROJECT` constant removed or replaced
- `src/mcp_guide/core/tool_decorator.py` — `_check_project_bound` must trigger template rendering rather than returning a static result
- `src/mcp_guide/render/cache.py` — template context builder must handle unbound sessions gracefully
- `src/mcp_guide/templates/_system/_project-root.mustache` — new file
- Existing specs `template-rendering`, `session-management`, `filesystem-interaction` have requirement-level changes
