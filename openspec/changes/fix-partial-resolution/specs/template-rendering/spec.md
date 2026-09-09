## ADDED Requirements

### Requirement: Canonically contained frontmatter partials
The system SHALL resolve each relative frontmatter partial reference from the
directory of its including template and SHALL load it only when the final
canonical file target, after independent partial-filename and extension
resolution, is contained within the configured document root. It SHALL accept
an absolute reference only when its final canonical target is contained within
that root. This resolution SHALL use server-side document-root containment and
SHALL NOT use client-filesystem resolution semantics. It SHALL not read, render,
or merge frontmatter from an unsafe partial target.

#### Scenario: Parent-relative partial remains inside the document root
- **WHEN** a nested template references a partial with `..` path components
- **AND** the final canonical partial target remains within the document root
- **THEN** the system SHALL render that partial using the existing partial
  composition behaviour

#### Scenario: Absolute partial reference remains inside the document root
- **WHEN** frontmatter names a partial with an absolute path whose final
  canonical target is inside the configured document root
- **THEN** the system SHALL load that partial

#### Scenario: Home-anchored or environment-variable partial reference
- **WHEN** frontmatter names a partial using home-anchored or
  environment-variable expansion syntax
- **THEN** the system SHALL reject that partial reference without expansion
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
- **AND** it SHALL log a non-sensitive warning
