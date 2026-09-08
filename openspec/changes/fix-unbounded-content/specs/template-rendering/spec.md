## ADDED Requirements

### Requirement: Canonically contained frontmatter partials
The system SHALL resolve each frontmatter partial reference relative to its
rendering template and SHALL load it only when the final canonical file target,
after extension resolution, is contained within the configured document root.
It SHALL not read, render, or merge frontmatter from an unsafe partial target.

#### Scenario: Parent-relative partial remains inside the document root
- **WHEN** a nested template references a partial with `..` path components
- **AND** the final canonical partial target remains within the document root
- **THEN** the system SHALL render that partial using the existing partial
  composition behaviour

#### Scenario: Absolute or home-anchored partial reference
- **WHEN** frontmatter names a partial with an absolute or home-anchored path
- **THEN** the system SHALL reject that partial reference
- **AND** it SHALL not read content from the named host path

#### Scenario: Relative partial escapes the document root
- **WHEN** a relative frontmatter partial reference canonically resolves outside
  the configured document root
- **THEN** the system SHALL reject that partial reference
- **AND** it SHALL not render the outside file's content

#### Scenario: In-root symlink points outside the document root
- **WHEN** a frontmatter partial reference resolves through a symlink whose
  canonical target is outside the configured document root
- **THEN** the system SHALL reject that partial reference
- **AND** it SHALL not read the symlink target

#### Scenario: One unsafe partial does not suppress safe rendering
- **WHEN** a template declares both a safe in-root partial and an unsafe
  partial reference
- **THEN** the system SHALL render the template and the safe partial
- **AND** it SHALL omit the unsafe partial without exposing its content

