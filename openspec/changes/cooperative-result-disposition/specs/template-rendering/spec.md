## MODIFIED Requirements

### Requirement: Centralized Instruction Resolution
The system SHALL provide a centralized function for resolving instructions from frontmatter that supports override semantics and type-based defaults.

#### Scenario: Important instruction override
- **WHEN** frontmatter includes `instruction: ! <text>`
- **THEN** the instruction SHALL be marked as important and override regular instructions

#### Scenario: Type-based default fallback
- **WHEN** no explicit instruction is provided in frontmatter
- **AND** the content type's disposition is not fully self-explanatory without one
- **THEN** the system SHALL use a type-based default instruction for the content type

#### Scenario: No default instruction when disposition is self-sufficient
- **WHEN** no explicit instruction is provided in frontmatter
- **AND** the content type's disposition alone conveys the required agent behavior
- **THEN** the system SHALL return no default instruction for that content type
- **AND** the rendered result SHALL still carry that content type as its disposition

#### Scenario: Instruction deduplication
- **WHEN** multiple sources provide the same instruction
- **THEN** the system SHALL deduplicate at sentence level
