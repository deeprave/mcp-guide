## MODIFIED Requirements

### Requirement: Centralized Instruction Resolution
The system SHALL provide a centralized function for resolving instructions from frontmatter that supports override semantics. No content type SHALL have a fabricated default instruction; a disposition alone, once taught to the agent, conveys the required behavior without a paired prose restatement.

#### Scenario: Important instruction override
- **WHEN** frontmatter includes `instruction: ! <text>`
- **THEN** the instruction SHALL be marked as important and override regular instructions

#### Scenario: Type-based default fallback
- **WHEN** no explicit instruction is provided in frontmatter
- **THEN** the system SHALL return no default instruction, regardless of content type
- **AND** the rendered result SHALL still carry its content type as its disposition

#### Scenario: Instruction deduplication
- **WHEN** multiple sources provide the same instruction
- **THEN** the system SHALL deduplicate at sentence level
