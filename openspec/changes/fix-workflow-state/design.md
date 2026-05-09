## Context

This change fixes two related workflow-state problems.

First, the `:status` / `guide://_status` command currently conflates "workflow
is enabled but not initialized yet" with "workflow is not enabled". The current
status template can tell the agent to send workflow file content even when
workflow tracking is disabled, which is misleading because no workflow
monitoring flow is active in that state.

Second, some project flags affect behavior that depends on long-lived task
manager subscribers or background checks, including workflow, client info, and
openspec. On startup, task enablement may intentionally be deferred until a
project is loaded because project flags are not available before then. Once a
project is loaded, disabled flag-gated tasks may unsubscribe themselves by
design.

The gap is what happens after that initial decision. Project flags can change at
runtime, and clients can switch between projects with different flag
configurations. The current task manager invalidates cached flags on project or
config change, but it does not reconcile the lifecycle of flag-gated tasks.

This is a cross-cutting change because it touches status rendering, workflow
bootstrap guidance, and feature-flag-driven runtime behavior.

## Goals / Non-Goals

**Goals:**
- Make status output distinguish clearly between workflow disabled and workflow
  enabled but uninitialized
- Keep workflow bootstrap instructions only for the workflow-enabled case
- Add bootstrap guidance for creating `.guide.yaml` when workflow is enabled
  but no workflow file exists yet
- Define reliable behavior for runtime changes to task-dependent project flags
- Define reliable behavior when switching between projects with different
  task-dependent flag configurations
- Add task-manager lifecycle hooks that can start and stop flag-gated tasks on
  demand without requiring MCP server or agent restart
- Keep the lifecycle design small, idempotent, serialized, and easy to test
  because task manager code is asynchronous and deadlock-prone

**Non-Goals:**
- Rework unrelated task scheduling or subscription architecture beyond the
  lifecycle hooks needed for flag-gated tasks
- Redesign the workflow file format beyond the minimum bootstrap requirement
- Change unrelated status output or template rendering behavior
- Change workflow semantics beyond clearer initialization and status behavior

## Decisions

### Distinguish disabled workflow from uninitialized workflow in the status template

The status command should branch on workflow enablement before it branches on
workflow state availability.

Required behavior:

- if workflow is disabled, show only that workflow is not enabled, optionally
  with simple user-facing guidance on how to enable it
- if workflow is enabled and a workflow state has not yet been received, show
  the existing setup guidance for sending workflow content
- if workflow is enabled and workflow state is available, render the normal
  workflow status section

This keeps the user-visible message aligned with actual system capability.

Alternative considered:
- Keep the current template behavior and rely on agent interpretation. Rejected
  because the current wording is factually wrong when workflow is disabled.

### Bootstrap missing workflow files only when workflow is enabled

When workflow is enabled but no workflow state has been received yet, the
agent-facing instruction should add one more bootstrap step: if `{{workflow.file}}`
does not exist at the project root, create it before sending content.

The initial file content should be:

- `phase: discussion`
- `issue:` with an explicit blank value

The explicit blank issue line is required because the current YAML
deserialization path expects the field to exist.

This keeps bootstrap behavior within the existing workflow monitoring flow
instead of introducing a separate initialization command.

Alternative considered:
- Auto-create the workflow file on the server side. Rejected because the
  current design expects the agent/client filesystem interaction path to create
  and send project-local state files.

### Reconcile flag-gated task lifecycle dynamically

For flags whose practical effect depends on long-lived tasks or subscriptions,
the task manager must reconcile task lifecycle dynamically. Restart guidance is
not an acceptable designed outcome because clients that switch projects are the
clients least able to use restart as normal workflow.

This applies at least to flags such as:

- `workflow`
- `allow-client-info`
- `openspec`

Reconciliation should run after:

- project load or project switch
- project flag changes
- global flag changes that affect the active project

The task manager should compare the desired task set for the current resolved
flags with the currently active managed task set, then:

- start missing managed tasks whose requirements are satisfied
- stop active managed tasks whose requirements are no longer satisfied
- leave already-correct tasks alone
- avoid duplicate subscriptions for the same managed task
- avoid holding task-manager locks while invoking task code that may call back
  into the task manager

The existing behavior where a task can unsubscribe itself if its flag is
disabled during initialization remains valid, but reconciliation must be able to
start the task again if a later project or flag state enables it.

Alternative considered:
- Require users to restart the MCP server or agent after task-dependent flag
  changes. Rejected because it is operationally poor for project-switching
  clients and leaves the task manager lifecycle model incorrect.

### Keep lifecycle ownership explicit

Not every task needs lifecycle reconciliation. Only managed task classes whose
behavior depends on feature flags or project context should participate.

Each managed task should have a single explicit registration describing:

- a stable managed task key
- the task factory or class
- the resolved flag or predicate required for activation
- any task-specific cleanup behavior needed when deactivated

The task manager should own managed task instances, while existing task
subscriptions should continue to own event delivery. This keeps lifecycle
reconciliation separate from low-level event fan-out.

Alternative considered:
- Infer managed tasks by scanning existing subscriptions. Rejected because it
  makes project-switch behavior implicit and increases the risk of duplicate or
  orphaned subscriptions.

### Serialize reconciliation to avoid async deadlocks

Task lifecycle reconciliation should be guarded so only one reconciliation runs
at a time. If project or config changes arrive while reconciliation is running,
the task manager should coalesce or queue another reconciliation pass rather
than running concurrently.

The implementation should avoid awaiting arbitrary task code while holding a
global task-manager mutation lock. The safer pattern is:

1. Resolve flags and compute a desired lifecycle plan
2. Snapshot current managed task state
3. Decide starts and stops
4. Execute start/stop operations outside shared-state locks where possible
5. Apply final managed-task registry updates in a narrow critical section

This is intentionally conservative because timer tasks, file-content events, and
session change callbacks can all interact with task manager state.

## Risks / Trade-offs

- [Lifecycle reconciliation deadlocks] -> serialize reconciliation, avoid
  awaiting task callbacks while holding shared task-manager locks, and test
  concurrent project/config-change scenarios
- [Duplicate subscriptions] -> use stable managed task keys and idempotent
  start/stop operations
- [Task state leaks across projects] -> clear or replace task-specific cached
  state when stopping managed tasks or switching projects where the task becomes
  disabled
- [Status template conditions drift from actual workflow enablement semantics] ->
  drive the status branches from workflow enablement first, then workflow state
- [Bootstrap guidance creates malformed workflow files] -> specify the minimum
  valid `.guide.yaml` content explicitly, including a blank `issue:` field
- [Lifecycle support grows too broad] -> limit the first implementation to
  explicit managed task registrations for known task-dependent flags

## Migration Plan

1. Update status rendering so workflow-disabled and workflow-uninitialized
   states are distinct
2. Update workflow bootstrap instructions so missing workflow files are created
   with valid initial content when workflow is enabled
3. Introduce managed task registration and idempotent start/stop hooks for
   flag-gated tasks
4. Reconcile managed task lifecycle after project load, project switch, and
   relevant flag changes
5. Validate the affected status, bootstrap, flag-change, and project-switch
   flows with focused tests and manual pause points

Rollback is straightforward:

- revert the status-template branch changes
- revert the workflow bootstrap instruction change
- disable managed task reconciliation and restore the previous startup-only task
  lifecycle behavior

## Open Questions

- Should workflow-disabled status output merely state that workflow is disabled,
  or should it also show a concise user-facing hint about which flag or command
  enables it?
- Which existing tasks should be included in the first managed-task registry
  beyond workflow, OpenSpec, and client-info?
- On project switch, which task-specific cached values should be cleared
  immediately versus left to be overwritten by the next task event?
