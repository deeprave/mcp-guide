## Context

The shared ConfigManager already snapshots configuration and publishes a coarse
`global_changed` / `project_changed` signal to affected Session instances.
Session listeners then receive only `on_config_changed(session)`.  The
Session-owned TaskManager consequently invalidates flags and restarts every
project task, while the template cache and other consumers cannot distinguish
what changed.  See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- Define an immutable, framework-neutral configuration-update value that
  describes one session's old effective state, new effective state, and scoped
  differences.
- Make Session own consumer registration, ordered dispatch, and failure
  isolation after project binding.
- Let TaskManager decide its actions from task-relevant differences, retaining
  unaffected tasks, caches, and instructions.
- Use the same path for local writes and watcher-detected external changes.

**Non-Goals:**

- Changing MCP tool arguments, protocol revisions, or configuration file
  format.
- Providing configuration migration for invalid/legacy project keys.
- Making unbound sessions apply project configuration.

## Decisions

### Use an effective per-session diff, not a raw file diff

ConfigManager will continue owning the whole validated snapshot and calculate
which global and strict `(project-name, hash)` entries changed.  Before
dispatch, each affected Session obtains its current effective project state and
constructs an update with old/new effective values plus named differences.
This avoids exposing unrelated project data and lets consumers act without
understanding persisted key layout.

Raw snapshot callbacks were considered, but would leak persistence details and
force every consumer to duplicate project selection and feature resolution.

### Introduce a dedicated configuration-update consumer protocol

Replace the coarse listener method with a protocol shaped as
`configuration_changed(update)`.  A session registers consumers when it binds;
registration is idempotent and cleanup discards them with the session.  The
Session dispatches in registration order, catches each consumer failure, and
does not let one failure block remaining consumers.

Keeping `on_config_changed(session)` was rejected because it cannot state
whether a notification is global, project-specific, or a no-op for a consumer.

### Serialize at the Session boundary and coalesce to latest state

Each Session owns an asynchronous update lock and a pending latest update slot.
ConfigManager may publish concurrently, but Session applies one update at a
time and replaces queued superseded work with the newest effective update.
Consumers therefore never run concurrently for the same Session and converge
on the latest configuration.

### Give TaskManager an explicit change-action planner

TaskManager compares task-relevant resolved flags from the update.  It
invalidates resolved-flag caches only when those values differ, and computes
start/stop/reconfigure actions per registered task rather than restarting the
entire project task set.  Category and collection changes remain visible to
other consumers but do not by themselves churn event handlers.

## Risks / Trade-offs

- [Resolved flags may depend on multiple configuration layers] → calculate
  effective values once per Session update and make those values the consumer
  contract.
- [A slow consumer delays later updates] → serialize and coalesce pending work;
  retain diagnostics for consumer duration and failure.
- [A consumer mutates configuration during dispatch] → publish a subsequent
  update after the active one; never recursively dispatch inside a consumer.

## Migration Plan

1. Add the update model and protocol alongside existing listener plumbing.
2. Migrate built-in consumers and delete the coarse callback once all are
   registered through Session.
3. Cover write, watcher, concurrency, no-op, and task-selectivity flows with
   isolated session tests.
4. Rollback consists of restoring the prior listener dispatch; no persisted
   configuration migration is required.
