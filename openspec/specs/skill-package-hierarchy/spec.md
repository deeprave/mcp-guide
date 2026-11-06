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
relative to the `_skills` category directory, and immutable complete frontmatter
excluding `name`.

#### Scenario: Share stable discovery across sessions

- **WHEN** two sessions use the same GuideRuntime while the private skills-root
  mtime is unchanged
- **THEN** both sessions SHALL resolve public skill names through the same
  runtime-owned discovery mapping

### Requirement: GuideSkill availability and catalogue metadata

Each GuideSkill record SHALL contain an immutable mapping of parsed
`requires-*` declarations, empty when none are present, and catalogue/resource
resolution metadata. The shared mapping SHALL not cache session-specific
availability decisions.

#### Scenario: GuideSkill has parsed requirement declarations
- **WHEN** a skill package declares requires-* frontmatter
- **THEN** its frozen GuideSkill record retains the parsed declarations

### Requirement: Skill discovery mapping freshness

The mapping SHALL retain effective filesystem mtime and population time. Its
freshness check SHALL use effective recursive mtime of relevant private-skills
files, so nested package changes invalidate the mapping. When
`guide-development` is enabled, discovery SHALL rebuild without using cache.

#### Scenario: Development bypasses discovery cache
- **WHEN** guide-development is enabled and a session requests skills
- **THEN** Guide rebuilds discovery without reusing the cached mapping

### Requirement: Skill discovery mapping coordination

GuideRuntime SHALL create or replace its mtime-aware discovery mapping under
the dedicated skill-discovery cache mutex.

The cache mutex SHALL be dedicated to skill-discovery cache access, SHALL be
non-reentrant, and SHALL NOT serialise unrelated configuration work.

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

### Requirement: Flat-layout compatibility

The system SHALL continue to discover and resolve existing one-directory skill
packages using their declared public names without requiring a migration.

#### Scenario: Retain an existing flat package

- **WHEN** `_skills/workflow-review/SKILL.md.mustache` declares `name: workflow-review`
- **THEN** `guide://$workflow-review` SHALL continue to resolve that package
