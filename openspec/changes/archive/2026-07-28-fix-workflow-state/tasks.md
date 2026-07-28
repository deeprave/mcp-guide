## 1. Status Workflow-State Messaging

- [x] 1.1 Update the status command template and any included workflow partial logic so workflow-disabled status is distinct from workflow-enabled but uninitialized status
- [x] 1.2 Ensure the workflow-disabled status path does not instruct the agent to send workflow file content and does not imply workflow monitoring is active
- [x] 1.3 Ensure the workflow-enabled but uninitialized status path retains workflow setup guidance only for the workflow-enabled case

## 2. Workflow Bootstrap Guidance

- [x] 2.1 Update workflow setup or monitoring instruction templates so missing workflow files are created only when workflow tracking is enabled
- [x] 2.2 Specify bootstrap content for a missing workflow file with `phase: discussion` and an explicit blank `issue:` line
- [x] 2.3 Add or update tests covering the workflow-enabled bootstrap path and the workflow-disabled status path

## 3. Project-Scoped Task Registration

- [x] 3.1 Audit existing `@task_init` users and classify which tasks are project-scoped versus import-time infrastructure
- [x] 3.2 Add regression tests proving existing `@task_init` import-time behavior remains intact for non-project-scoped infrastructure
- [x] 3.3 Add a new `@task_register` decorator that records project-scoped task classes without instantiating them
- [x] 3.4 Ensure `@task_register` does not encode flags, activation predicates, factories, or cache policy
- [x] 3.5 Add unit tests for project-scoped task class registration, duplicate handling, and no-instantiation behavior
- [x] 3.6 Pause for manual review of the registration model before wiring lifecycle restart

## 4. Serialized Project-Scoped Lifecycle Restart

- [x] 4.1 Add task manager lifecycle hooks to stop active project-scoped task instances, unsubscribe them, and start fresh registered task instances
- [x] 4.2 Add task-owned async startup behavior so each task can decide whether and how to subscribe for the current project context
- [x] 4.3 Add optional task-owned cleanup/stop behavior for project-scoped state that cannot be handled by unsubscribe alone
- [x] 4.4 Add tests that initial project bind starts registered task classes only after project context is available
- [x] 4.5 Add tests that project switch stops all active project-scoped task instances and creates fresh instances, even when flags appear unchanged
- [x] 4.6 Add tests that project/global config changes restart project-scoped tasks and cause task-owned activation policy to re-run
- [x] 4.7 Add serialized or coalesced lifecycle restart so concurrent project/config changes cannot run stop/start mutation concurrently
- [x] 4.8 Add async tests for concurrent lifecycle triggers proving the final task set belongs to the latest project context and no deadlock occurs
- [x] 4.9 Pause for manual testing of restart behavior with a focused local scenario before migrating runtime tasks

## 5. Runtime Task Migration

- [x] 5.1 Migrate `WorkflowMonitorTask` from import-time `@task_init` instantiation to project-scoped `@task_register` discovery
- [x] 5.2 Move `WorkflowMonitorTask` subscription and workflow flag checks into task-owned async startup behavior
- [x] 5.3 Migrate `ClientContextTask` from import-time `@task_init` instantiation to project-scoped `@task_register` discovery
- [x] 5.4 Move `ClientContextTask` subscription and activation checks into task-owned async startup behavior
- [x] 5.5 Migrate `OpenSpecTask` from import-time `@task_init` instantiation to project-scoped `@task_register` discovery
- [x] 5.6 Move `OpenSpecTask` subscription and activation checks into task-owned async startup behavior
- [x] 5.7 Keep non-project-scoped tasks on `@task_init` and verify server startup still imports modules needed for registration
- [x] 5.8 Clear project-scoped volatile cache entries and queued instructions when lifecycle restart stops or replaces task instances
- [x] 5.9 Add focused tests that workflow, OpenSpec, and client-info each independently decide whether to activate for the current project
- [x] 5.10 Pause for manual project-switch testing before broad validation

## 6. Validation

- [x] 6.1 Run the relevant template, feature-flag, workflow, task-manager, and status-related test suite
- [x] 6.2 Verify the final behavior for:
  - workflow disabled status
  - workflow enabled but uninitialized status
  - workflow bootstrap creation guidance
  - `@task_register` records classes without import-time instantiation
  - initial project bind starts project-scoped tasks after project context exists
  - project switching stops all old project-scoped task instances and starts fresh ones
  - runtime config changes restart project-scoped tasks for the current project
  - workflow, OpenSpec, and client-info each make independent activation decisions
  - repeated and concurrent lifecycle restart does not duplicate subscriptions or deadlock
