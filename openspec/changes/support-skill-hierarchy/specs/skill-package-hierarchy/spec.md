## Purpose

Allow server-owned Guide skill packages to be organised hierarchically while
retaining stable, flat public names and portable resource URIs for agents.

## ADDED Requirements

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

### Requirement: Flat-layout compatibility

The system SHALL continue to discover and resolve existing one-directory skill
packages using their declared public names without requiring a migration.

#### Scenario: Retain an existing flat package

- **WHEN** `_skills/workflow-review/SKILL.md.mustache` declares `name: workflow-review`
- **THEN** `guide://$workflow-review` SHALL continue to resolve that package
