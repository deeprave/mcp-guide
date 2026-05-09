## Why

Workflow-related status and feature-flag behavior is currently misleading in
two ways. The `:status` / `guide://_status` output can imply that workflow
state is available even when workflow is disabled, and task eligibility is not
reconciled when project flags become available, change at runtime, or change as
the active project changes.

This matters because workflow, OpenSpec, and client-info behavior depend on
long-lived background tasks or subscriptions. CLI agents usually keep one
project per process, so stale task lifecycle state has not been visible often.
Clients that switch projects expose the gap: restarting the MCP server or agent
is least convenient precisely when dynamic task reconciliation is needed.

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
- Add task manager lifecycle hooks that reconcile flag-gated tasks when:
  - a project is loaded
  - the active project changes
  - project or global flags change at runtime
- Start tasks whose required flags are now enabled and stop tasks whose required
  flags are now disabled, without requiring an MCP server or agent restart
- Make reconciliation safe for async task-manager operation by keeping it
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
- `task-manager`: task-dependent feature flag changes and project changes should
  dynamically start and stop the corresponding background task behavior

## Impact

- Affected code is likely to include:
  - status command templates and workflow partials
  - workflow monitoring/setup instruction templates
  - task manager task/subscription activation behavior
  - feature flag and project-change handling
  - tests for async lifecycle reconciliation and deadlock avoidance
- Affected systems:
  - workflow status display
  - workflow monitoring bootstrap flow
  - runtime feature-flag-driven task availability
  - project switching across different flag configurations
