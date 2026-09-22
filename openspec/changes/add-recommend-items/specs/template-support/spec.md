## ADDED Requirements

### Requirement: Recommendation template helper
The common template context SHALL expose the `recommend` helper for every
template rendering surface. It SHALL collect recommendation items on the same
render result that carries template errors, without emitting the helper's
enclosed text into normal rendered content.

#### Scenario: Helper is available in a skill template
- **WHEN** a Guide skill entrypoint uses the `recommend` helper
- **THEN** the entrypoint render records its recommendation item
- **AND** the rendered skill instructions do not include the helper marker

#### Scenario: Helper is available in an ordinary content template
- **WHEN** a command, workflow, context, or ordinary content template uses the
  `recommend` helper
- **THEN** its render records the same structured recommendation item
