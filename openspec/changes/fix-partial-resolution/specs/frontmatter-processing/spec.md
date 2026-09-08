## MODIFIED Requirements

### Requirement: Partial Template Support (Basic)
The system SHALL parse the `partials` field in frontmatter and validate every
partial reference before template rendering. A reference SHALL be a relative
path interpreted from the rendering template's location; it SHALL not be an
absolute or home-anchored path. Relative references, including those containing
parent components, SHALL be permitted only when the final canonical target is
contained within the configured document root.

#### Scenario: Partials field parsing
- **WHEN** frontmatter contains a `partials` field with relative references
  whose canonical targets are inside the document root
- **THEN** the system SHALL parse and accept those partial references
- **AND** provide them for template composition

#### Scenario: Parent-relative in-root partial parsing
- **WHEN** frontmatter contains a relative partial reference with `..`
  components whose final canonical target is inside the document root
- **THEN** the system SHALL accept the reference
- **AND** preserve existing nested-template composition behaviour

#### Scenario: Unsafe partial reference
- **WHEN** frontmatter contains an absolute, home-anchored, or
  canonically-out-of-root partial reference
- **THEN** the system SHALL reject that reference
- **AND** it SHALL not allow the reference to cause a host file read

