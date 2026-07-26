## Context

This change fixes two related workflow-state problems.

First, the `:status` / `guide://_status` command currently conflates "workflow
is enabled but not initialized yet" with "workflow is not enabled". The current
status template can tell the agent to send workflow file content even when
workflow tracking is disabled, which is misleading because no workflow
monitoring flow is active in that state.

Second, several long-lived subscribers and background checks are project-scoped.
Examples include workflow monitoring, client context collection, and OpenSpec
detection. Those tasks should not need to decide their final runtime behavior at
module import time because project context and project flags may not be bound
yet.

The gap is lifecycle ownership. Clients can switch projects, and project config
can change at runtime. The current import-time task initialization path makes
tasks instantiate too early, then rely on self-unsubscribe behavior when the
current project is not ready or a task decides it should not run. The task
manager needs to own project-scoped task start/stop orchestration while each
task class keeps ownership of its own activation policy.

This is a cross-cutting change because it touches status rendering, workflow
bootstrap guidance, and feature-flag-driven runtime behavior.

## Goals / Non-Goals

**Goals:**
- Make status output distinguish clearly between workflow disabled and workflow
  enabled but uninitialized
- Keep workflow bootstrap instructions only for the workflow-enabled case
- Add bootstrap guidance for creating `.guide.yaml` when workflow is enabled
  but no workflow file exists yet
- Define reliable behavior for runtime project config changes that affect
  project-scoped tasks
- Define reliable behavior when switching projects
- Add task-manager lifecycle hooks that restart project-scoped tasks for the
  current project without requiring MCP server or agent restart
- Add an explicit project-scoped task registration path without changing the
  existing `@task_init` import-time behavior
- Keep the lifecycle design small, idempotent, serialized, and easy to test
  because task manager code is asynchronous and deadlock-prone

**Non-Goals:**
- Rework unrelated task scheduling or subscription architecture beyond the
  lifecycle hooks needed for project-scoped tasks
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

### Restart project-scoped task lifecycle dynamically

For behavior that depends on long-lived project-scoped tasks or subscriptions,
the task manager must control lifecycle dynamically. Restart guidance is not an
acceptable designed outcome because clients that switch projects are the clients
least able to use MCP server or agent restart as normal workflow.

This applies at least to project-scoped task classes such as:

- `WorkflowMonitorTask`
- `ClientContextTask`
- `OpenSpecTask`

Lifecycle restart should run after:

- initial project bind
- project switch
- project config changes
- global config changes that affect the active project

On project switch, the task manager must stop all currently active
project-scoped task instances and start fresh instances for the new project
context. This is not an incremental "keep running unless disabled" operation:
project-scoped tasks may cache paths, project data, queued and tracked
instructions, command availability, or client state that belongs to the previous
project.

The task manager should:

- maintain the registry of project-scoped task classes
- stop and unsubscribe active project-scoped task instances during project
  lifecycle restart
- instantiate each registered project-scoped task class after project context is
  available
- invoke an async task-owned startup hook so the task can decide whether and how
  to subscribe
- avoid duplicate active instances for the same registered task class
- clear queued and tracked instructions so pending setup or reminder prompts
  from the previous project cannot be emitted after restart
- avoid holding task-manager locks while invoking task code that may call back
  into the task manager

Alternative considered:
- Require users to restart the MCP server or agent after project switches or
  task-dependent config changes. Rejected because it is operationally poor for
  project-switching clients and leaves the task manager lifecycle model
  incorrect.

### Use `@task_register` for project-scoped task discovery

Do not repurpose `@task_init`. It has existing import-time singleton semantics
and may be appropriate for infrastructure such as `TaskManager` or other
non-project-scoped tasks.

Add a new `@task_register` decorator for project-scoped tasks. The
decorator should only register the class in a module-level registry. It should
not instantiate the class, check flags, subscribe to events, or encode task
policy.

Each registered task class owns its own activation policy. It may inspect
project flags, project config, client context, command availability, or any
other relevant inputs during its async startup hook. The task manager must not
assume a 1:1 flag-to-task relationship.

The task manager owns active project-scoped task instances, while subscriptions
continue to own event delivery. This keeps lifecycle orchestration separate from
task policy and low-level event fan-out.

Alternative considered:
- Extend `@task_init` with flags or activation predicates. Rejected because it
  has wider import-time semantics and would oversimplify task-owned policy.
- Infer project-scoped tasks by scanning existing subscriptions. Rejected
  because it makes project-switch behavior implicit and increases the risk of
  duplicate or orphaned subscriptions.

### Serialize lifecycle restart to avoid async deadlocks

Project-scoped task lifecycle restart should be guarded so only one lifecycle
mutation runs at a time. If project or config changes arrive while restart is
running, the task manager should serialize the work or queue another pass rather
than running concurrent stop/start operations.

The implementation should avoid awaiting arbitrary task code while holding a
global task-manager mutation lock. The safer pattern is:

1. Snapshot active project-scoped task instances
2. Clear the active-instance registry in a narrow critical section
3. Stop/unsubscribe old instances outside shared-state locks where possible
4. Instantiate registered task classes for the current project context
5. Await each task-owned startup hook outside shared-state locks where possible
6. Record active instances that actually started in a narrow critical section

This is intentionally conservative because timer tasks, file-content events, and
session change callbacks can all interact with task manager state.

## Risks / Trade-offs

- [Lifecycle restart deadlocks] -> serialize restart work, avoid
  awaiting task callbacks while holding shared task-manager locks, and test
  concurrent project/config-change scenarios
- [Duplicate subscriptions] -> track active project-scoped instances by class or
  stable task id and make restart idempotent
- [Task state leaks across projects] -> stop all project-scoped tasks on project
  switch and clear project-scoped task, cache, and instruction state before
  starting fresh tasks
- [Status template conditions drift from actual workflow enablement semantics] ->
  drive the status branches from workflow enablement first, then workflow state
- [Bootstrap guidance creates malformed workflow files] -> specify the minimum
  valid `.guide.yaml` content explicitly, including a blank `issue:` field
- [Lifecycle support grows too broad] -> limit the first implementation to
  explicit `@task_register` project-scoped task classes and leave `@task_init`
  behavior intact for existing import-time infrastructure

## Migration Plan

1. Update status rendering so workflow-disabled and workflow-uninitialized
   states are distinct
2. Update workflow bootstrap instructions so missing workflow files are created
   with valid initial content when workflow is enabled
3. Add `@task_register` for project-scoped task class discovery, without
   changing `@task_init`
4. Move participating project-scoped tasks from import-time instantiation to
   project-scoped registration
5. Add task-manager stop/start lifecycle hooks that restart all registered
   project-scoped tasks after project bind, project switch, and relevant config
   changes
6. Let each task class decide during async startup whether it should subscribe
   for the current project context
7. Validate the affected status, bootstrap, config-change, and project-switch
   flows with focused tests and manual pause points

Rollback is straightforward:

- revert the status-template branch changes
- revert the workflow bootstrap instruction change
- disable project-scoped task lifecycle restart and restore the previous
  import-time task initialization behavior for migrated tasks

## Implementation Clarifications

- Workflow-disabled status output should state plainly that workflow tracking is
  disabled and omit `send_file_content` instructions. This change should not add
  new enablement commands or broaden status output beyond the workflow-state fix.
- `@task_register` should register task classes only. It should not take flags,
  predicates, cache keys, or factories.
- Each project-scoped task should expose task-owned async startup behavior and
  decide whether to subscribe based on the current project context.
- Project switches must restart all registered project-scoped tasks, not only
  tasks whose resolved flags differ.
- When project-scoped tasks are stopped or restarted, clear volatile
  project-scoped cache entries and queued or tracked instructions that can
  otherwise produce stale prompts or template context:
  - workflow: `workflow_state`, `workflow_file_path`, `workflow_change_content`
  - OpenSpec: `openspec_available`, `openspec_version`, `openspec_status`,
    `openspec_show`, `openspec_changes`
  - client-info: `client_os_info`, `client_context_info`
