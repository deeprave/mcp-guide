## Context

See [proposal.md](proposal.md) for the motivation.  Project configuration is
currently represented by an immutable `Project` model, while the configuration
manager owns the machine-level YAML document.  `clone_project` reconstructs its
destination with only categories and collections, discarding other project
configuration.  OpenSpec CLI state is currently attached to that project model,
which makes a machine-wide executable check repeat for every project.

## Goals / Non-Goals

**Goals:**

- Preserve every transferable project setting when cloning, without changing the
  destination identity.
- Represent OpenSpec CLI state once as the global structured `openspec-state`
  feature flag.
- Remove existing per-project state and force a fresh check for enabled projects.
- Bound version-check commands across all projects on a machine to one per
  rolling 24-hour period.

**Non-Goals:**

- Change how a project root is detected or selected.
- Share OpenSpec state between machines or persist it in the repository.
- Cache project-specific OpenSpec content, active changes, or specifications as
  global state.
- Add a configurable version-check interval.
- Make OpenSpec enabled merely because machine-wide CLI state is available.

## Decisions

### Model OpenSpec state as a structured global feature flag

Store machine-wide OpenSpec state in the global-only `openspec-state` feature
flag. The existing feature-flag persistence API is the read/write boundary; no
new configuration API or top-level configuration model is needed. Serialise it
as:

```yaml
feature_flags:
  openspec-state:
    validated: "true"
    version: "1.10.0"
    checked: "0.0"
```

The feature-flag system permits structured mapping values with string members,
so `validated` and `checked` are stored as canonical strings. OpenSpec-domain
helpers will parse and validate this mapping and serialise complete replacement
values for writes. An invalid check writes `validated: "false"`, omits
`version`, and records `checked` as a decimal UTC Unix timestamp string.

Remove `openspec_validated` and `openspec_version` from `Project`. Consumers
that need CLI state will receive it through the global feature-flag service or
template context. Project-specific OpenSpec filesystem detection remains
project-bound. The existing `project_flags.openspec` setting also remains on
each Project: it controls whether that project uses OpenSpec, independently of
global CLI availability and version state. It is the exclusive enablement gate:
there is no global OpenSpec flag or fallback that can enable the integration for
a Project.

Register `openspec-state` as feature-only with validation for that structured
mapping. Register `openspec` as project-only, so the normal project-to-global
resolution hierarchy cannot fall back to a global enablement value.

### React to existing configuration-change publication

The runtime already publishes global feature-flag and active-project changes to
affected Sessions. Their `TaskManager` invalidates its resolved flags and
restarts registered project tasks. OpenSpec will use this existing lifecycle,
not add a parallel callback mechanism. When the current Project's `openspec`
flag becomes enabled, the restarted `OpenSpecTask` reads `openspec-state` and,
when it is absent or expired, queues its availability instruction. A successful
availability response then queues the version-check instruction. When the flag
becomes disabled, task restart stops and unsubscribes that session's OpenSpec
task.

Writing `openspec-state` also uses the existing global feature-flag publication
path. Every affected task re-evaluates state after restart, but the newly written
`checked` timestamp prevents another availability or version instruction from
being queued during the 24-hour interval.

### Treat a completed check as a 24-hour attempt

The task will compare `time.time()` with global `openspec-state.checked`; it may issue
a version check only when the timestamp is absent or at least 86,400 seconds
old.  Once a response is processed, it records the current UTC Unix timestamp
as a decimal string even if the response is invalid or no version can be parsed.
A successful parse sets `validated="true"` and records the version; an
unsuccessful response sets `validated="false"` and omits the version.

Recording failed attempts prevents a missing or malformed CLI response from
causing repeated prompts in every newly bound project.  The alternative—only
timestamping successful checks—would violate the intended machine-wide throttle
when OpenSpec is unavailable.

When an OpenSpec-enabled Project first needs the integration and no global state
has been stored, the task performs that availability and version check, then
sets the complete `openspec-state` feature-flag value. A disabled Project does not
initialise or refresh global OpenSpec state.

### Remove legacy fields without migration

Legacy `openspec_validated` and `openspec_version` values are not authoritative
machine state and SHALL NOT be copied into `openspec-state`. Loading accepts the
old fields only so existing configuration remains readable; the next project
save omits them. If that Project enables OpenSpec, the existing configuration
publication and task lifecycle starts its OpenSpec task, which performs fresh
availability and version checks when global state is absent or expired.

### Clone transferables explicitly and preserve destination identity

Construct the cloned project from the source's transferable fields while taking
`name`, `key`, and `hash` from the already bound destination.  In merge mode,
mapping fields (categories, collections, project flags, and exports) merge with
source values winning duplicate keys; permission/read-path lists are replaced
by the source lists because unioning path permissions can unintentionally widen
access.  In replacement mode, every transferable field is replaced.

Copying a serialised project wholesale was rejected because it could overwrite
the destination identity and potentially import deprecated fields.

## Risks / Trade-offs

- [A user upgrades with legacy versions] → Discard them and force a fresh check
  rather than select potentially stale data.
- [A temporary failed version check delays another check] → The 24-hour bound is
  intentional; the stored invalid state makes the outcome visible and avoids
  repeated agent prompts.
- [Merge semantics for path lists surprise a caller] → Document and test that
  source lists replace destination lists, avoiding accidental permission union.
- [Older clients still read per-project fields] → Load legacy fields during the
  migration window, but write only the global `openspec-state` representation.
- [Global state accidentally enables OpenSpec for every project] → Keep
  `project_flags.openspec` project-scoped and cover enabled and disabled projects
  in task and template tests.

## Migration Plan

1. Define the structured global feature-flag state and its parsing/validation
   rules while accepting legacy project data for read compatibility.
2. Remove legacy fields whenever the configuration is saved, without creating or
   modifying the global `openspec-state` flag.
3. Refactor OpenSpec task and template consumers to use that state, then add
   the 24-hour check guard.
4. Extend clone behaviour and cover merge/replacement behaviour, migration, and
   check timing with tests.

Rollback remains possible by restoring a version that still accepts the legacy
fields; the normalised global `openspec-state` feature flag is ignored by older
clients that do not consume it.
