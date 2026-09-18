## Context

The shared ConfigManager already snapshots configuration and publishes a coarse
`global_changed` / `project_changed` signal directly to affected Session
instances. Session listeners then receive only `on_config_changed(session)`.
The Session-owned TaskManager consequently invalidates flags and restarts every
project task, while the template cache and other consumers cannot distinguish
what changed. ConfigManager also duplicates GuideRuntime's session ownership by
maintaining its own Session registry. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- Define an immutable, framework-neutral configuration-update value that
  describes one session's old effective state, new effective state, and scoped
  differences.
- Keep raw validated configuration snapshots and publication entirely within
  ConfigManager's configuration domain, with no Session registration or
  lifecycle dependency.
- Make GuideRuntime select only active, live, bound sessions and derive their
  effective updates from each snapshot delta.
- Make Session own consumer registration, ordered dispatch, and failure
  isolation after project binding.
- Let TaskManager decide its actions from task-relevant differences, retaining
  unaffected tasks, caches, and instructions.
- Give every project-task instance an explicit activation capability that is
  the sole authority for that task's mutable manager state.
- Use the same path for local writes and watcher-detected external changes.

**Non-Goals:**

- Changing MCP tool arguments, protocol revisions, or configuration file
  format.
- Providing configuration migration for invalid/legacy project keys.
- Making unbound sessions apply project configuration.

## Decisions

### Publish a configuration snapshot delta to GuideRuntime

ConfigManager will retain the previous and current immutable validated
configuration snapshots, including global feature-flag values and valid strict
project entries. It will emit one `ConfigurationSnapshotDelta` to GuideRuntime
after every internal write or watcher refresh that changes either image.

The delta is configuration-layer data. It identifies whether global flags
changed and which strict `(project-name, hash)` entries changed, and retains the
old/new snapshots needed to determine effective flag values. ConfigManager will
not register Sessions, select affected Sessions, or invoke session listeners.

GuideRuntime owns the authoritative active, inflight, and expiring session
collections. It receives the delta, ignores unbound, expiring, disposed, and
otherwise non-live Session instances, then selects candidates from its live
bound Session registry. A global-flag change makes every live bound Session a
candidate; a project-entry change makes only Sessions with the corresponding
strict active identity candidates. Failure reconciling one Session is isolated
from the remaining candidates.

Each server process owns its own ConfigManager, GuideRuntime, watcher, and
active sessions. In multi-process deployments, every process independently
observes persisted changes and reconciles only the sessions it owns.

Initial root binding is deliberately not a candidate for Session update
delivery: it has not yet entered the live bound registry. ConfigManager
therefore resolves and returns the requested Project from its final validated
snapshot after the lookup/create operation and before publishing that snapshot
delta. If an external writer removed the entry in that interval, it repeats the
lookup so a Session cannot be promoted with a Project that disagrees with the
published image.

### Use an effective per-session diff, not a raw file diff

GuideRuntime derives each candidate's old/new effective state directly from the
immutable snapshots and that Session's strict binding identity. The projection
is a pure runtime-level operation: it does not call back into ConfigManager or
expose raw snapshot data to Session consumers. It includes only known
configuration fields and resolved feature flags needed by consumers, excluding
unneeded persisted flag values.

GuideRuntime dispatches only a non-empty `ConfigurationUpdate` to a Session.
For example, a project override can mask a changed global flag, so that Session
does not receive a consumer update despite being a global-change candidate.
This avoids exposing unrelated project data and lets consumers act without
understanding persisted key layout.

### Introduce a dedicated configuration-update consumer protocol

Replace the coarse listener method with a protocol shaped as
`configuration_changed(update)`.  A session registers consumers when it binds;
registration is idempotent and cleanup discards them with the session.  The
Session dispatches in registration order, catches each consumer failure, and
does not let one failure block remaining consumers.

Keeping `on_config_changed(session)` was rejected because it cannot state
whether a notification is global, project-specific, or a no-op for a consumer.

### Snapshot selection is coordinated; delivery is Session-serialised

The existing configuration coordination lock serialises snapshot replacement
and GuideRuntime candidate selection with root transitions. It is not held
while awaiting Session consumer delivery: doing so would make slow consumers
block configuration writes and unrelated Session transitions.

After candidate selection, GuideRuntime enqueues a candidate's effective update
without awaiting consumer work. A Session confirms it remains live and bound
before applying its queued update. If expiry or a root transition supersedes it,
the Session discards the stale work. Equivalent watcher notifications with
unchanged snapshots produce no delta.

### Serialize at the Session boundary and coalesce to latest state

Each Session owns a single-consumer update runner and a pending latest update
slot. GuideRuntime may reconcile overlapping snapshot deltas concurrently, but
each Session applies one update at a time and replaces queued superseded work
with the newest revision. This queue serialises configuration application
without adding a lock hierarchy around consumer delivery.
Consumers therefore never run concurrently for the same Session and converge
on the latest configuration.

Effective updates retain immutable project and feature-flag projections for
consumer delivery. The Session materialises a separate project model before
rebinding its delegate, so a consumer cannot mutate the Session's active
configuration or another consumer's update view.

### Give TaskManager an explicit change-action planner

TaskManager compares task-relevant resolved flags from the update.  It
invalidates resolved-flag caches only when those values differ, and computes
start/stop/reconfigure actions per registered task rather than restarting the
entire project task set.  Category and collection changes remain visible to
other consumers but do not by themselves churn event handlers.

TaskManager attributes cache writes and queued acknowledgement instructions to
the registered task that produced them during startup or event dispatch. When a
configuration action stops or replaces a selected handler, it retires that
handler's attributed cache and instruction state before activating the
replacement. State produced by unaffected handlers, and unowned Session-level
instructions, remains valid and is retained.

### Make TaskActivation the project-task state boundary

The existing task API passes the general `TaskManager` to project tasks. That
allows a task to mutate manager-wide subscriptions, cache, and instruction
state, so the manager must infer the producing task from ambient callback
context. Generation and ownership `ContextVar` guards close individual races,
but every new callback path becomes another boundary that must be remembered.

Each project-task instance will instead receive one `TaskActivation` when it
is created. `TaskActivation` is a narrow, task-owned capability: it exposes
the project-task operations needed to read resolved flags and cached values,
subscribe to events, queue or acknowledge instructions, and write task-owned
cache entries. It retains the owning task identity and lifecycle state
internally. Project tasks will receive the activation during `start()` and
retain it for their event, timer, and delivery work; they will no longer be
given the general `TaskManager` for mutable operations.

TaskManager remains the orchestrator and continues to expose its existing
manager-wide APIs for Session-level and non-project producers. It creates an
activation before invoking project-task `start()`, records it with the active
task instance, and routes project-task subscriptions and tracked instruction
delivery through that activation. The activation is therefore also captured by
deferred acknowledgement-delivery callbacks rather than reconstructing their
authority from the callback's ambient execution context.

Retirement is one idempotent activation transition. Before a task is stopped
or replaced, TaskManager retires its activation: it blocks later state writes,
removes that activation's pending and tracked instructions, clears only cache
entries it still owns, and removes its subscriptions. A start, event, timer,
tool, or deferred delivery callback that resumes after retirement observes the
same retired activation and cannot repopulate state. Cleanup operations that
only discard already-owned resources remain safe and idempotent.

This replaces task lifecycle generation and owner `ContextVar` state with the
activation's direct authority. A generation may remain internal diagnostic
metadata, but it must not be required to attribute or reject task writes. The
existing lifecycle lock continues to serialise activation, retirement, and
replacement; the design introduces no second lock hierarchy.

## Risks / Trade-offs

- [Resolved flags may depend on multiple configuration layers] → GuideRuntime
  calculates effective values from each immutable snapshot and makes those
  values the consumer contract.
- [A slow consumer delays later updates] → serialize and coalesce pending work;
  retain diagnostics for consumer duration and failure.
- [A consumer mutates configuration during dispatch] → publish a subsequent
  update after the active one; never recursively dispatch inside a consumer.
- [Migrating every project task broadens the internal API change] → migrate the
  complete registered project-task set together and retain manager-wide APIs
  only for explicitly unowned Session-level producers. This removes the mixed
  ownership model rather than carrying it forward as a compatibility layer.

## Migration Plan

1. Add the snapshot-delta and effective-update models, and move Session
   registry ownership from ConfigManager to GuideRuntime.
2. Migrate built-in consumers and delete the coarse callback once all are
   registered through Session.
3. Introduce `TaskActivation`, migrate the complete registered project-task
   set away from mutable `TaskManager` operations, and remove the ambient
   task-generation and ownership guards.
4. Cover write, watcher, active-session selection, expiry, concurrency, no-op,
   task-selectivity, and activation-retirement flows with isolated runtime and
   session tests.
5. Rollback consists of restoring the prior listener dispatch; no persisted
   configuration migration is required.
