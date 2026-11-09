## ADDED Requirements

### Requirement: Handoff-context is enabled unless explicitly disabled

The `handoff-context` feature flag SHALL resolve to the default shared handoff
target when absent at both project and global scope. An explicit boolean
`false` at the effective scope SHALL disable handoff context. This exception
to ordinary absent-flag resolution SHALL be documented prominently in
feature-flag guidance.

#### Scenario: Handoff context is unset

- **GIVEN** neither project nor global configuration sets `handoff-context`
- **WHEN** Guide resolves handoff context for a bound project
- **THEN** it SHALL resolve the default shared handoff target

#### Scenario: Handoff context is explicitly disabled

- **GIVEN** the effective `handoff-context` value is boolean `false`
- **WHEN** Guide resolves handoff context for a bound project
- **THEN** it SHALL not resolve a handoff target
