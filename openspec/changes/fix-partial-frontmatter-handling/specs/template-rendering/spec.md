## MODIFIED Requirements

### Requirement: Template Partial Inclusion
The system SHALL support including partial templates with frontmatter metadata that can override parent template behavior.

#### Scenario: Partial overrides parent instruction
- **WHEN** a partial template includes frontmatter with `instruction: ! <text>`
- **THEN** the partial's instruction SHALL override the parent template's instruction

#### Scenario: Partial provides type metadata
- **WHEN** a partial template includes `type:` frontmatter
- **THEN** the partial's type SHALL be used when the partial is rendered

#### Scenario: Conditional display behavior
- **WHEN** a template conditionally includes a partial based on data availability
- **THEN** the partial's frontmatter SHALL control whether content is displayed or treated as instructions
