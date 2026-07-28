## Why

Workflow-related status and project-scoped task behavior are currently misleading in
two ways. The `:status` / `guide://_status` output can imply that workflow
state is available even when workflow is disabled, and task eligibility is not
restarted cleanly when project context becomes available, project config changes
at runtime, or the active project changes.

This matters because workflow, OpenSpec, and client-info behavior depend on
long-lived background tasks or subscriptions. CLI agents usually keep one
project per process, so stale task lifecycle state has not been visible often.
Clients that switch projects expose the gap: restarting the MCP server or agent
is least convenient precisely when dynamic project-scoped task lifecycle is
needed.

## What Changes

- Make `:status` distinguish clearly between:
  - workflow disabled
  - workflow enabled but no workflow state has been received yet
  - workflow enabled with current workflow state available
- When workflow is disabled, remove agent-facing instructions that imply
  `send_file_content` should be used for workflow state
- When workflow is enabled but workflow state is missing, keep the existing
  setup guidance and add explicit agent instructions to create `.guide.yaml`
  if it does not yet exist, with:
  - `phase: discussion`
  - `issue:` present but blank
- Add task manager lifecycle hooks that restart project-scoped tasks when:
  - a project is loaded
  - the active project changes
  - project or global config changes at runtime
- Add a `@task_register` discovery path for project-scoped task classes while
  leaving existing `@task_init` import-time behavior intact
- Let each project-scoped task decide during async startup whether it should
  subscribe for the current project context
- Make lifecycle restart safe for async task-manager operation by keeping it
  idempotent, serialized, and testable in small steps

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow-context`: status output and workflow setup guidance should reflect
  whether workflow is disabled, enabled-but-uninitialized, or active
- `workflow-monitoring`: workflow initialization guidance should support
  bootstrap creation of `.guide.yaml` when workflow monitoring is enabled but no
  state file exists yet
- `task-manager`: project binds, project switches, and relevant config changes
  should dynamically restart project-scoped background task behavior

## Impact

- Affected code is likely to include:
  - status command templates and workflow partials
  - workflow monitoring/setup instruction templates
  - task manager task/subscription lifecycle behavior
  - project and config change handling
  - tests for async lifecycle restart and deadlock avoidance
- Affected systems:
  - workflow status display
  - workflow monitoring bootstrap flow
  - runtime project-scoped task availability
  - project switching across different project contexts
