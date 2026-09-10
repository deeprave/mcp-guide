## MODIFIED Requirements

### Requirement: Partial Template Support (Basic)
The system SHALL parse the `partials` field in frontmatter and validate every
partial reference before template rendering. Relative references SHALL be
interpreted from the rendering template's location. Absolute references SHALL
be permitted only when their final canonical target is contained within the
configured document root. Home-anchored and environment-variable expansion
syntax SHALL be invalid. Relative references, including those containing parent
components, SHALL be permitted only when the final canonical target is
contained within the configured document root. A reference names the partial
without its leading underscore; underscore filename derivation and extension
handling are separate from reference resolution. The derived underscore-prefixed
filename SHALL remain excluded from ordinary command and category document
discovery.

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
- **WHEN** frontmatter contains a home-anchored, environment-variable, or
  canonically-out-of-root partial reference
- **THEN** the system SHALL exclude that reference from the rendering set
- **AND** it SHALL log a non-sensitive warning without failing the parent
  template
- **AND** it SHALL not allow the reference to cause a host file read
