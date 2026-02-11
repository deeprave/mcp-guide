## ADDED Requirements

### Requirement: Centralized Instruction Resolution
The system SHALL provide a centralized function for resolving instructions from frontmatter that supports override semantics and type-based defaults.

#### Scenario: Important instruction override
- **WHEN** frontmatter includes `instruction: ! <text>`
- **THEN** the instruction SHALL be marked as important and override regular instructions

#### Scenario: Type-based default fallback
- **WHEN** no explicit instruction is provided in frontmatter
- **THEN** the system SHALL use type-based default instruction for the content type

#### Scenario: Instruction deduplication
- **WHEN** multiple sources provide the same instruction
- **THEN** the system SHALL deduplicate at sentence level

### Requirement: Template Partial Frontmatter Merging
The system SHALL merge partial template frontmatter with parent template frontmatter using centralized instruction resolution.

#### Scenario: Partial overrides parent instruction
- **WHEN** a partial template includes frontmatter with `instruction: ! <text>`
- **THEN** the partial's instruction SHALL override the parent template's instruction

#### Scenario: Partial provides type metadata
- **WHEN** a partial template includes `type:` frontmatter
- **THEN** the partial's type SHALL be preserved and used for instruction resolution

#### Scenario: Conditional display behavior
- **WHEN** a template conditionally includes a partial based on data availability
- **THEN** the partial's frontmatter SHALL control whether content is displayed or treated as instructions
