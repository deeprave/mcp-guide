## 1. Configuration Update Contract

- [ ] 1.1 Define immutable effective-configuration and change-set types covering global flags, active-project categories, collections, project flags, and task-relevant resolved flags.
- [ ] 1.2 Define the configuration-update consumer protocol and replace the coarse Session listener configuration callback with its typed update method.
- [ ] 1.3 Add Session-owned registration, binding-time setup, cleanup, ordered dispatch, error isolation, and per-session update coalescing.

## 2. Shared Publication and Session Reconciliation

- [ ] 2.1 Refactor ConfigManager write and watcher publication to preserve old/new validated snapshots and identify affected global and strict project identities.
- [ ] 2.2 Build the old/new effective update for each affected bound Session, refresh its active project only when required, and avoid dispatching no-op updates.
- [ ] 2.3 Migrate built-in Session consumers, including template context caching and URI/startup listeners, to the configuration-update protocol and selective invalidation behavior.

## 3. Task Lifecycle Actions

- [ ] 3.1 Refactor TaskManager configuration handling to consume the typed update and invalidate resolved flags only when effective flag values change.
- [ ] 3.2 Add a task action planner that retains unaffected handlers and applies only necessary start, stop, restart, subscription, cache, and instruction changes.
- [ ] 3.3 Serialize/coalesce task lifecycle changes with project switches and verify the final task set belongs to the latest effective configuration.

## 4. Verification

- [ ] 4.1 Add isolated Session and ConfigManager tests for internal writes, external watcher changes, scoped project/global diffs, no-op publication, listener ordering, failures, and concurrent updates.
- [ ] 4.2 Add TaskManager lifecycle tests for task-relevant versus category/collection-only updates, handler retention, activation changes, cache invalidation, and concurrent project/config updates.
- [ ] 4.3 Update affected documentation and run the repository validation suite.
