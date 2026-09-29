## Context

The current skills implementation discovers only direct `_skills/*/SKILL.md`
packages and uses the directory name as the public identity. That makes public
names portable but prevents server-side organisation by subject. See
`proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**

- Separate server-side package location from the stable name exposed to agents
- Support nested packages without changing the public Guide skill URI shape
- Preserve existing flat package behaviour
- Share one mtime-aware discovery mapping across sessions of a GuideRuntime
- Reorganise bundled Git and workflow packages without exposing their paths

**Non-Goals:**

- Nested public skill identifiers or public URI paths
- Changes to the standard local `SKILL.md` package format
- Automatic migration of third-party package trees

## Decisions

### Use entrypoint frontmatter as the public identity

Discovery will recursively locate renderable `SKILL.md` package roots. It will
parse each entrypoint's frontmatter and use its required `name` as the unique
public identifier. This lets `_skills/workflow/review/` expose
`workflow-review` and keeps the catalogue, tool, and URI surface flat.

The alternative, deriving a public identifier from nested directories, would
make package reorganisation a client-visible breaking change and reintroduce
slash-delimited skill identifiers that standard local skill catalogues do not
normally use.

### Resolve members through the discovered package record

The catalogue will retain a record mapping each public name to its validated
package root. Selection will first resolve that name, then resolve any member
path relative to the mapped root using the existing literal-member validation.
Directory structure will not be inferred from the requested URI.

### Keep discovery state on GuideRuntime

Skill packages are server-owned rather than session-scoped. GuideRuntime will
therefore own a dictionary keyed by public skill name. Each value is one frozen
`GuideSkill` record containing its name, package root relative to the `_skills`
category directory, immutable complete frontmatter excluding `name`, and an
immutable mapping of parsed `requires-*` declarations (empty when absent), plus
the metadata needed to advertise and resolve the package. The mapping also retains
the effective recursive skills-tree mtime used to validate it and the time at
which it was populated. That mtime is the maximum relevant mtime within the
private skills tree, so nested entrypoint or member changes invalidate
discovery even when the root directory's own mtime does not change. For five
minutes after population, normal operation returns the mapping without
filesystem validation or timestamp updates. Cache creation and replacement are
serialised with the runtime's mutex-style coordination so concurrent sessions
cannot observe or publish partially refreshed discovery state. A failed
validation or refresh retains the last valid mapping and logs a diagnostic.

Normal operation reuses the mapping while the skills-root mtime is unchanged.
When `guide-development` is enabled, discovery will not reuse that cache so
template authors see changes immediately; its rebuilds still use the same
runtime coordination. This is a dedicated, non-reentrant mutex for skill
cache access only; it is unrelated to configuration-transition coordination.

### Apply feature requirements per session

The runtime mapping represents valid discovered packages and is not an
availability cache for one session. The cached `requires-*` declarations are
evaluated against the requesting session's effective feature-flag state before
a catalogue advertises a package or a resource resolves it. A package failing
that evaluation is unavailable to that session, without changing the shared
runtime mapping or another session's availability.

### Virtualise public retrieval paths

The directory stored in the runtime mapping is private implementation state.
Catalogue and retrieval responses will identify an entrypoint or member using
the public skill name, for example `git-commit/SKILL.md`, rather than its
server-side `_skills/git/commit/` path.

### Treat invalid declarations as unavailable packages

An absent, blank, invalid, or duplicate public name makes a package
unavailable. Discovery logs a diagnostic identifying the affected package but
continues serving independent valid packages. This prevents arbitrary or
ambiguous resource routing.

### Organise triage by the work being decided

The server-side triage category will contain three deliberately distinct
packages:

- `_skills/triage/items/` exposes `triage-items`, the generic, sequential
  decision workflow for a stable inventory.
- `_skills/triage/pr/` exposes `triage-pr`, the pull-request author's workflow
  for deciding reviewer feedback and performing explicitly authorised local or
  remote follow-up.
- `_skills/triage/review/` exposes `triage-review`, the workflow-bound
  collation workflow for the current review issue.

The former `just-one`, `git-pr-triage`, and `workflow-triage` public names are
retired rather than retained as aliases. Their package paths and every bundled
recommendation will be updated in the same change.

### Separate generic decision records from review inventories

`triage-items` selects its inventory from an explicit user target first, then
from the most relevant established context, such as a just-collated review or
active pull-request feedback. It asks only when no clear inventory is
available. It preserves source evidence and processes exactly one item at a
time, but does not assume the current checkout owns the resulting work.

When a canonical decision inventory already exists, such as
`{{path.documents}}Reviews/<issue>.json` for `triage-review`, the skill updates
that record. Existing pull-request comment seen-state remains collection state,
not a decision ledger. For a new durable record, use
`{{path.documents}}Triage/<derived-key>.json`, with an optional identity such
as pull-request number, workflow issue, or user-provided label. Without an
existing inventory or a request for persistence, retain the decision record in
the conversation.

After all decisions, `triage-items` presents accepted, varied, declined,
deferred, and unresolved items plus their next actions. Those actions may be
local implementation, a report, a pull-request response or disposition,
another agent's work, or no action. The skill requires explicit user authority
before performing any local changes or external action.

### Collate every applicable workflow review source

`triage-review` remains dependent on `workflow-review` and its current issue.
For an initial collation, it must discover and include every valid source
record for that issue, regardless of the agent or session that created it; it
must not infer that reports it just produced are the complete source set. For
an incremental re-triage, the existing canonical `Reviews/<issue>.json`
inventory is the cutoff: preserve its relevant decisions and consider only
newer or updated source records. A user may instead explicitly request a full
historical re-collation. The skill then updates the issue-specific canonical
inventory and recommends `triage-items` when the user wants serial decisions.

### Keep handover outside skill contracts

Bundled skill instructions will not direct agents to update handoff context.
The user or project workflow may establish a handover preference independently
of a specific skill.

### Bind workflow-review sources to the producing reviewer

Each workflow-review assignment provides its reviewer with its own agent and
model identity. The reviewer derives its report path and record identity solely
from that pair as `<agent-name>-<model-name>`, normalised to lowercase
hyphenated form. The coordinator determines a version only for that exact
destination, without exposing another reviewer's identity or findings.

The alternative—role suffixes such as `-heavy` and `-light`, or selecting a
name from existing content—allows one reviewer to overwrite or misattribute
another reviewer's evidence.

### Preserve a compact, preference-led triage experience

`triage-pr` does not prescribe a grouped or serial default. It adapts to the
user's normal preference and may present either form. `triage-items` presents
each prioritised item as `X/N [P?] <short description>` and combines brief
target and scope values on one `Target/Scope:` line. During incremental
workflow triage, resolved findings remain historical records and only pending
or newly collated findings are presented for decision.

## Risks / Trade-offs

- [A duplicate name hides a skill unexpectedly] → Log the conflicting paths
  and omit both packages until an author selects unique names
- [Recursive discovery expands scan work] → Reuse the existing mtime-aware
  discovery cache with an effective recursive mtime and limit traversal to the
  private skills root
- [A package is moved] → Its public name and URI remain unchanged, so only
  server-side source references need updating

## Migration Plan

1. Require a `name` for newly discovered package roots
2. Move bundled `git-*` and `workflow-*` packages to their nested locations
   while retaining their declared public names
3. Validate discovery, duplicate handling, runtime cache behaviour, nested
   retrieval, virtual public paths, and unchanged flat-package retrieval
4. Move and rename the three triage packages, update their recommendations and
   documentation, and retire their former public identities
5. Roll back by restoring flat-only discovery; bundled names are harmless
   metadata in that state
