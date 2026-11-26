# Spec Delta

## MODIFIED Requirements

### Requirement: Hierarchical package discovery

The system SHALL discover a skill package at any descendant directory of the
private `_skills` root when that directory contains a renderable `SKILL.md`
entrypoint.

#### Scenario: Discover a nested package

- **WHEN** `_skills/guide/review/SKILL.md.mustache` is present
- **THEN** the system SHALL include that package in skill discovery

### Requirement: Public skill name declaration

Every discovered skill package SHALL declare a non-empty public `name` in its
entrypoint frontmatter. The public name SHALL be globally unique among all
discovered skill packages and SHALL be the package's only advertised identity.

#### Scenario: Advertise a nested package by its declared name

- **WHEN** `_skills/guide/review/SKILL.md.mustache` declares `name: guide-review`
- **THEN** the catalogue SHALL advertise `guide-review` rather than the
  directory path `workflow/review`

#### Scenario: Advertise consolidated triage packages by their declared names

- **WHEN** discovered Guide packages declare `name: guide-triage` and
  `name: guide-sequence`
- **THEN** the catalogue SHALL advertise those declared public names
- **AND** SHALL not advertise `triage-review`, `triage-pr`, or `triage-items`

#### Scenario: Reject duplicate declared names

- **WHEN** two discovered packages declare the same public `name`
- **THEN** neither ambiguous package SHALL be advertised or resolved and the
  system SHALL log a clear configuration warning

### Requirement: Flat public resource resolution

The system SHALL resolve a selected skill and its package members from the
declared public name, independent of the package's server-side directory path.

#### Scenario: Retrieve a nested package entrypoint

- **WHEN** a client reads `guide://$guide-review`
- **THEN** the system SHALL return the rendered `SKILL.md` entrypoint from the
  package declaring `guide-review`

#### Scenario: Retrieve a nested package member

- **WHEN** a client reads a member under `guide://$guide-review/`
- **THEN** the system SHALL resolve that member relative to the package that
  declares `guide-review`

### Requirement: Virtual public retrieval paths

The system SHALL not expose a skill package's server-side directory path in a
catalogue or retrieval response. It SHALL identify returned files with the
public skill name followed by their package-relative path.

#### Scenario: Report a nested entrypoint with its public path

- **WHEN** `_skills/guide/git/commit/SKILL.md.mustache` declares `name: guide-git-commit`
  and the entrypoint is retrieved
- **THEN** the response SHALL identify the file as `guide-git-commit/SKILL.md` and
  SHALL not expose `_skills/guide/git/commit/`

### Requirement: Flat-layout compatibility

The system SHALL continue to discover and resolve existing one-directory skill
packages using their declared public names without requiring a migration.

#### Scenario: Retain an existing flat package

- **WHEN** `_skills/custom-review/SKILL.md.mustache` declares `name: guide-review`
- **THEN** `guide://$guide-review` SHALL continue to resolve that package
