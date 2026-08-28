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
- Represent OpenSpec CLI state once in global configuration with a typed,
  explicit schema.
- Migrate existing persisted state deterministically and force a fresh check
  where the legacy version cannot be trusted.
- Bound version-check commands across all projects on a machine to one per
  rolling 24-hour period.

**Non-Goals:**

- Change how a project root is detected or selected.
- Share OpenSpec state between machines or persist it in the repository.
- Cache project-specific OpenSpec content, active changes, or specifications as
  global state.
- Add a configurable version-check interval.

## Decisions

### Model OpenSpec as a dedicated global configuration object

Add a typed global OpenSpec state object owned by the top-level configuration,
with `validated`, `version`, and `checked` fields.  Serialise it as:

```yaml
openspec:
  validated: true
  version: 1.10.0
  checked: 0.0
```

This is deliberately a sibling of `feature_flags`, rather than a feature-flag
value: it has a fixed structured contract and a lifecycle unrelated to flag
resolution.  A generic structured feature flag would bypass the existing
generic flag type rules and obscure the distinction between per-project policy
and installed executable state.

Remove `openspec_validated` and `openspec_version` from `Project`.  Consumers
that need CLI state will receive it from the configuration manager or template
context.  Project-specific OpenSpec filesystem detection remains project-bound.

### Treat a completed check as a 24-hour attempt

The task will compare `time.time()` with global `openspec.checked`; it may issue
a version check only when the timestamp is absent or at least 86,400 seconds
old.  Once a response is processed, it records the current UTC Unix timestamp
as a float even if the response is invalid or no version can be parsed.  A
successful parse sets `validated=true` and records the version; an unsuccessful
response sets `validated=false` and clears the version.

Recording failed attempts prevents a missing or malformed CLI response from
causing repeated prompts in every newly bound project.  The alternative—only
timestamping successful checks—would violate the intended machine-wide throttle
when OpenSpec is unavailable.

### Migrate legacy fields on configuration normalisation

When loading legacy project data, collect distinct non-null
`openspec_version` values.  A single distinct value initialises global
`openspec.version`; multiple values leave it null.  In both cases, initialise
`checked` as null so the next eligible run confirms the installed CLI version.
Legacy validation may initialise the global boolean only when no current global
OpenSpec value exists; a new check remains authoritative.

On the next write, omit both deprecated fields from every project entry.  This
allows old configuration files to load while converging them to the new shape.
Using the first encountered legacy version was rejected because project order
would make the outcome arbitrary.

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

- [A user upgrades with conflicting legacy versions] → Clear the version and
  force a fresh check rather than select a potentially stale value.
- [A temporary failed version check delays another check] → The 24-hour bound is
  intentional; the stored invalid state makes the outcome visible and avoids
  repeated agent prompts.
- [Merge semantics for path lists surprise a caller] → Document and test that
  source lists replace destination lists, avoiding accidental permission union.
- [Older clients still read per-project fields] → Load legacy fields during the
  migration window, but write only the global representation.

## Migration Plan

1. Introduce the global model and configuration-manager read/write support while
   accepting legacy project data.
2. Normalise legacy values into global state and remove the old fields whenever
   the configuration is saved.
3. Refactor OpenSpec task and template consumers to use global state, then add
   the 24-hour check guard.
4. Extend clone behaviour and cover merge/replacement behaviour, migration, and
   check timing with tests.

Rollback remains possible by restoring a version that still accepts the legacy
fields; the normalised global `openspec` mapping is ignored by older models that
allow extra configuration fields.
