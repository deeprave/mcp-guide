## 1. Status Workflow-State Messaging

- [ ] 1.1 Update the status command template and any included workflow partial logic so workflow-disabled status is distinct from workflow-enabled but uninitialized status
- [ ] 1.2 Ensure the workflow-disabled status path does not instruct the agent to send workflow file content and does not imply workflow monitoring is active
- [ ] 1.3 Ensure the workflow-enabled but uninitialized status path retains workflow setup guidance only for the workflow-enabled case

## 2. Workflow Bootstrap Guidance

- [ ] 2.1 Update workflow setup or monitoring instruction templates so missing workflow files are created only when workflow tracking is enabled
- [ ] 2.2 Specify bootstrap content for a missing workflow file with `phase: discussion` and an explicit blank `issue:` line
- [ ] 2.3 Add or update tests covering the workflow-enabled bootstrap path and the workflow-disabled status path

## 3. Task-Dependent Flag Change Behavior

- [ ] 3.1 Identify existing task subscribers, startup registration paths, and flag gates for `workflow`, `openspec`, and `allow-client-info`
- [ ] 3.2 Add tests documenting current behavior for project-load deferral and disabled flag self-unsubscribe, without changing behavior
- [ ] 3.3 Add a managed task registration model with stable task keys, activation predicates, and factories, but do not wire reconciliation yet
- [ ] 3.4 Add unit tests for the managed task registry covering duplicate registration, desired-state calculation, and no-op reconciliation plans
- [ ] 3.5 Pause for manual review/testing of the registration model before wiring it into live task manager events

## 4. Serialized Task Lifecycle Reconciliation

- [ ] 4.1 Add task manager start/stop hooks for managed tasks using idempotent operations and narrow critical sections
- [ ] 4.2 Add tests that starting an enabled managed task creates exactly one active subscription and repeated starts are no-ops
- [ ] 4.3 Add tests that stopping a disabled managed task unsubscribes it and clears only the task-specific lifecycle state required for correctness
- [ ] 4.4 Add serialized or coalesced reconciliation so concurrent project/config changes cannot run lifecycle mutation concurrently
- [ ] 4.5 Add async tests for concurrent reconciliation triggers proving the final task set matches latest resolved flags and no deadlock occurs
- [ ] 4.6 Pause for manual testing of start/stop behavior with a focused local scenario before wiring project and flag change callbacks

## 5. Project And Flag Change Wiring

- [ ] 5.1 Reconcile managed tasks after project load or project switch, after resolved flags are invalidated for the new project
- [ ] 5.2 Reconcile managed tasks after project flag changes that affect task-dependent flags
- [ ] 5.3 Reconcile managed tasks after global flag changes that affect task-dependent flags for the active project
- [ ] 5.4 Add tests for switching from workflow-enabled project to workflow-disabled project and back again
- [ ] 5.5 Add tests for enabling and disabling `workflow` at runtime without restarting the MCP server or agent
- [ ] 5.6 Add tests for `openspec` and `allow-client-info` runtime flag changes according to their managed task registrations
- [ ] 5.7 Pause for manual project-switch testing before broad validation

## 6. Validation

- [ ] 6.1 Run the relevant template, feature-flag, workflow, task-manager, and status-related test suite
- [ ] 6.2 Verify the final behavior for:
  - workflow disabled status
  - workflow enabled but uninitialized status
  - workflow bootstrap creation guidance
  - workflow task starts when enabled at runtime
  - workflow task stops when disabled at runtime
  - project switching reconciles task state
  - repeated and concurrent reconciliation does not duplicate subscriptions or deadlock
