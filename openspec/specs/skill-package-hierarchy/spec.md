# skill-package-hierarchy Specification

## Purpose

Allow server-owned Guide skill packages to be organised hierarchically while
retaining stable, flat public names and portable resource URIs for agents.

## Requirements

### Requirement: Hierarchical package discovery

The system SHALL discover a skill package at any descendant directory of the
private `_skills` root when that directory contains a renderable `SKILL.md`
entrypoint.

#### Scenario: Discover a nested package

- **WHEN** `_skills/workflow/review/SKILL.md.mustache` is present
- **THEN** the system SHALL include that package in skill discovery

### Requirement: Public skill name declaration

Every discovered skill package SHALL declare a non-empty public `name` in its
entrypoint frontmatter. The public name SHALL be globally unique among all
discovered skill packages and SHALL be the package's only advertised identity.

#### Scenario: Advertise a nested package by its declared name

- **WHEN** `_skills/workflow/review/SKILL.md.mustache` declares `name: workflow-review`
- **THEN** the catalogue SHALL advertise `workflow-review` rather than the
  directory path `workflow/review`

#### Scenario: Reject duplicate declared names

- **WHEN** two discovered packages declare the same public `name`
- **THEN** neither ambiguous package SHALL be advertised or resolved and the
  system SHALL log a clear configuration warning

### Requirement: Flat public resource resolution

The system SHALL resolve a selected skill and its package members from the
declared public name, independent of the package's server-side directory path.

#### Scenario: Retrieve a nested package entrypoint

- **WHEN** a client reads `guide://$workflow-review`
- **THEN** the system SHALL return the rendered `SKILL.md` entrypoint from the
  package declaring `workflow-review`

#### Scenario: Retrieve a nested package member

- **WHEN** a client reads a member under `guide://$workflow-review/`
- **THEN** the system SHALL resolve that member relative to the package that
  declares `workflow-review`

### Requirement: Runtime-scoped discovery mapping

The system SHALL retain a discovery dictionary on GuideRuntime, shared by its
sessions and keyed by public skill name. Each dictionary value SHALL be one
frozen `GuideSkill` record containing that public name, the package root
relative to the `_skills` category directory, immutable complete frontmatter
excluding `name`, an immutable mapping of parsed `requires-*` declarations
(empty when none are present), and the metadata needed for catalogue and
resource resolution. The mapping SHALL retain its effective filesystem mtime
and population time. It SHALL create or replace that mtime-aware mapping under
the runtime's mutex-style coordination. Its freshness check SHALL use the
effective recursive mtime of relevant files in the private skills tree, so
nested package changes invalidate the mapping. When the `guide-development`
feature flag is enabled, the system SHALL rebuild discovery without reusing the
cached mapping. The shared mapping SHALL not cache session-specific
availability decisions.

The cache mutex SHALL be dedicated to skill-discovery cache access, SHALL be
non-reentrant, and SHALL NOT serialise unrelated configuration work.

#### Scenario: Share stable discovery across sessions

- **WHEN** two sessions use the same GuideRuntime while the private skills-root
  mtime is unchanged
- **THEN** both sessions SHALL resolve public skill names through the same
  runtime-owned discovery mapping

#### Scenario: Refresh changed discovery safely

- **WHEN** the effective recursive mtime of the private skills tree changes
  while sessions request skills
- **THEN** the system SHALL serialise creation or replacement of the refreshed
  discovery mapping using the runtime's mutex-style coordination

#### Scenario: Reuse a recently populated mapping without I/O

- **WHEN** a non-development session requests skills less than five minutes
  after the runtime populated a valid discovery mapping
- **THEN** the system SHALL return that mapping without filesystem validation
- **AND** it SHALL not update the mapping's population time or effective mtime

#### Scenario: Preserve a valid mapping when refresh fails

- **GIVEN** the runtime has a valid discovery mapping
- **WHEN** filesystem validation or discovery later fails
- **THEN** the system SHALL retain the valid mapping
- **AND** it SHALL log a diagnostic rather than publish an empty mapping

#### Scenario: Bypass cache during development

- **WHEN** `guide-development` is enabled and a session requests skills
- **THEN** the system SHALL perform discovery without reusing the cached
  mapping

### Requirement: Session-specific skill availability

Before advertising or resolving a package from the shared runtime mapping, the
system SHALL evaluate the cached `requires-*` declarations against the
requesting session's effective feature flags. A package that does not satisfy
those requirements SHALL be unavailable to that session without being removed
from the runtime mapping.

#### Scenario: Restrict a cached skill for one session

- **GIVEN** a cached package declares `requires-example-flag: true`
- **AND** one session resolves `example-flag` as true while another resolves it
  as false
- **WHEN** both sessions request the skill catalogue or the package resource
- **THEN** the first session SHALL be able to advertise and resolve the package
- **AND** the second session SHALL not advertise or resolve it
- **AND** the runtime mapping SHALL remain available for either session's
  subsequent eligibility evaluation

### Requirement: Virtual public retrieval paths

The system SHALL not expose a skill package's server-side directory path in a
catalogue or retrieval response. It SHALL identify returned files with the
public skill name followed by their package-relative path.

#### Scenario: Report a nested entrypoint with its public path

- **WHEN** `_skills/git/commit/SKILL.md.mustache` declares `name: git-commit`
  and the entrypoint is retrieved
- **THEN** the response SHALL identify the file as `git-commit/SKILL.md` and
  SHALL not expose `_skills/git/commit/`

### Requirement: Bundled hierarchical organisation

The system SHALL organise bundled `git-*`, `workflow-*`, and triage skill
packages in matching nested directories while preserving declared public names,
except for the deliberately retired `just-one`, `git-pr-triage`, and
`workflow-triage` identifiers.

#### Scenario: Retain a relocated bundled skill's public identity

- **WHEN** the bundled Git commit package is stored below `_skills/git/commit/`
- **THEN** the catalogue and `guide://$git-commit` SHALL continue to expose and
  resolve `git-commit`

#### Scenario: Expose triage packages by their renamed public identities

- **WHEN** the bundled packages are stored below `_skills/triage/items/`,
  `_skills/triage/pr/`, and `_skills/triage/review/`
- **THEN** the catalogue SHALL expose `triage-items`, `triage-pr`, and
  `triage-review`
- **AND** it SHALL not advertise `just-one`, `git-pr-triage`, or
  `workflow-triage`

### Requirement: Flat-layout compatibility

The system SHALL continue to discover and resolve existing one-directory skill
packages using their declared public names without requiring a migration.

#### Scenario: Retain an existing flat package

- **WHEN** `_skills/workflow-review/SKILL.md.mustache` declares `name: workflow-review`
- **THEN** `guide://$workflow-review` SHALL continue to resolve that package

### Requirement: Generic item triage

The `triage-items` skill SHALL process a complete, stable inventory one item at
a time. It SHALL select an explicit user target first and otherwise derive the
most relevant available inventory from context. It SHALL preserve source
evidence, record explicit dispositions including deferred decisions, and keep
implementation or external actions separate until the user explicitly
authorises them. A deferred decision SHALL record its rationale and any revisit
condition, and SHALL remain outside the pending inventory unless the user
explicitly requests a revisit.

When an existing canonical decision inventory applies, the skill SHALL update
it. When persistence is requested without such an inventory, it SHALL use a
durable decision ledger below `{{path.documents}}Triage/` with an identity that
does not require a workflow issue.

#### Scenario: Triage a non-workflow inventory

- **WHEN** a user supplies a stable list of findings without a workflow issue
- **THEN** `triage-items` SHALL process that list without requiring
  `Reviews/<issue>.json`
- **AND** it SHALL keep the result conversational unless an existing decision
  record applies or the user requests persistence

#### Scenario: Exclude a deferred item from later triage

- **WHEN** the user defers an item during `triage-items`
- **THEN** the decision record SHALL preserve the deferred decision and its
  rationale
- **AND** a later triage run SHALL not present that item as pending unless the
  user explicitly requests a revisit

### Requirement: Pull-request author triage

The `triage-pr` skill SHALL help a pull-request author decide reviewer feedback
and its appropriate response. It SHALL select grouped reporting or a serial
`triage-items` walkthrough according to the user's normal preference. It SHALL
not apply code changes, post replies, resolve conversations, or change
pull-request disposition without explicit user authority.

#### Scenario: Preserve authority at pull-request action boundaries

- **WHEN** a pull-request author uses `triage-pr` to assess reviewer feedback
- **THEN** the skill SHALL recommend the proposed response or action
- **AND** it SHALL wait for explicit user authority before changing code,
  posting a reply, resolving a conversation, or changing pull-request state

### Requirement: Workflow review collation

The `triage-review` skill SHALL remain tied to the current workflow issue and
shall combine all eligible review-source records for that issue. For an initial
collation, every valid source record is eligible regardless of its agent or
session. For an incremental re-triage, the existing canonical inventory SHALL
be the cutoff and only newer or updated source records are eligible, unless the
user explicitly requests a full historical re-collation. The skill SHALL not
assume that reports created during the current review are the complete source
set.

The skill SHALL preserve declined and deferred decisions in the canonical
inventory. Matching deferred findings SHALL remain excluded from subsequent
triage unless the user explicitly requests a revisit or full historical
re-collation.

#### Scenario: Collate reports beyond the current agent's output

- **WHEN** an initial workflow review collation has source records from
  multiple agents or sessions
- **THEN** `triage-review` SHALL include every valid source record in its
  canonical inventory

#### Scenario: Incrementally update a prior collation

- **WHEN** a canonical inventory already exists and the user has not requested
  full historical re-collation
- **THEN** `triage-review` SHALL preserve its relevant decisions
- **AND** it SHALL consider only source records newer than that inventory or
  updated after its cutoff
- **AND** it SHALL present only pending and newly collated findings for a new
  decision, retaining resolved and deferred findings as history

#### Scenario: Add deferred findings to the handoff context

- **WHEN** the effective `handoff-context` flag is enabled and triage records
  one or more deferred findings
- **THEN** the rendered `triage-review` guidance SHALL instruct the agent to add
  each deferred finding and its rationale to the handoff context

### Requirement: Workflow review source identity

The `workflow-review` skill SHALL require each reviewer to write its source
record using only that reviewer's own assigned agent and model identities. The
path and composite reviewer identity SHALL use the lowercase hyphenated form
`<agent-name>-<model-name>`. The source record SHALL identify that same agent
name and model name. A reviewer SHALL NOT reuse, infer, or adopt either
identity component from an existing source record, another reviewer, or
unrelated prompt content, and SHALL NOT append review-role or effort suffixes.

#### Scenario: Independent reviewers receive distinct identities

- **WHEN** workflow-review dispatches two reviewers with different assigned
  agent and model identities
- **THEN** each reviewer SHALL write only
  `Reviews/<issue>/<its-agent-name>-<its-model-name>.json`
- **AND** each source record SHALL identify its own assigned agent and model
- **AND** neither reviewer SHALL overwrite or claim the other reviewer's record

### Requirement: Skill-neutral handover

Bundled skill instructions SHALL NOT direct an agent to update a handoff
context file.

#### Scenario: Deliver skill guidance without a handoff directive

- **WHEN** an agent reads a bundled skill entrypoint
- **THEN** its instructions SHALL not direct the agent to update a handoff
  context file

### Requirement: Compact prioritised item triage

When an inventory supplies priority, target, and scope, `triage-items` SHALL
present an item as `X/N [P?] <short description>` followed by one brief
`Target/Scope: <target>, <scope>` line.

#### Scenario: Present a prioritised review finding compactly

- **WHEN** triage processes a finding with priority, target, and scope
- **THEN** it SHALL show the priority in the heading
- **AND** it SHALL combine brief target and scope values on one line
