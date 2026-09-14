## 1. Configuration Update Contract

- [x] 1.1 Define immutable configuration-snapshot-delta, effective-configuration, and change-set types covering global flags, active-project categories, collections, project flags, and task-relevant resolved flags.
- [x] 1.2 Define the configuration-update consumer protocol and replace the coarse Session listener configuration callback with its typed update method.
- [x] 1.3 Add GuideRuntime-owned active-session selection and Session-owned registration, binding-time setup, cleanup, ordered dispatch, error isolation, and single-consumer queued per-session update coalescing.

## 2. Shared Publication and Session Reconciliation

- [x] 2.1 Refactor ConfigManager write and watcher publication to preserve old/new validated snapshots, including global flags, and publish a snapshot delta without registering or handling Sessions; initial root binding returns the project from that final image.
- [x] 2.2 Have GuideRuntime select active, live, bound candidate Sessions from each delta; build their old/new effective updates from the snapshots and strict binding identity, refresh their active project only when required, and avoid dispatching no-op updates.
- [x] 2.3 Migrate built-in Session consumers, including template context caching and URI/startup listeners, to the configuration-update protocol and selective invalidation behavior.

## 3. Task Lifecycle Actions

- [x] 3.1 Refactor TaskManager configuration handling to consume the typed update and invalidate resolved flags only when effective flag values change.
- [x] 3.2 Add a task action planner that retains unaffected handlers and applies only necessary start, stop, restart, subscription, cache, and instruction changes, including retiring state owned by a stopped or replaced handler.
- [x] 3.3 Serialize/coalesce task lifecycle changes with project switches and verify the final task set belongs to the latest effective configuration.
- [x] 3.4 Introduce a `TaskActivation` capability and migrate the registered project-task contract so task startup and callbacks use it instead of mutable `TaskManager` APIs.
- [x] 3.5 Move project-task subscription, cache, instruction, acknowledgement, and deferred delivery ownership into `TaskActivation`; retire it atomically and idempotently before task stop or replacement, removing ambient owner/generation guards.
- [x] 3.6 Migrate every registered project task to the activation API, retaining manager-wide mutable APIs only for explicitly unowned Session-level producers.

## 4. Verification

- [x] 4.1 Add isolated ConfigManager, GuideRuntime, and Session tests for internal writes, external watcher changes, scoped project/global diffs, unbound and expiring-session exclusion, no-op publication, listener ordering, failures, concurrent updates, and an external write during initial binding.
- [x] 4.2 Add TaskManager lifecycle tests for task-relevant versus category/collection-only updates, handler retention, activation changes, cache invalidation, and concurrent project/config updates.
- [x] 4.3 Update affected documentation and run the repository validation suite.
- [x] 4.4 Add lifecycle regressions proving that retired activations reject late startup, event, timer, tool, and acknowledgement-delivery writes while unaffected active tasks retain their state.
