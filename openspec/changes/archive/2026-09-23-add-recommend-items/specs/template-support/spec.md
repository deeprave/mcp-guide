## ADDED Requirements

### Requirement: Recommendation template helper
The common template context SHALL expose the `recommend` helper for every
template rendering surface. Rendering SHALL append each recommendation's
footnote directly to the rendered document before returning it. Result,
content, queue, listener, and response-adapter layers SHALL NOT carry
recommendation state.

#### Scenario: Helper is available in a skill template
- **WHEN** a Guide skill entrypoint uses the `recommend` helper
- **THEN** the entrypoint render includes the fluent reference and its footnote
- **AND** the rendered skill instructions do not include the helper marker

#### Scenario: Helper is available in an ordinary content template
- **WHEN** a command, workflow, context, or ordinary content template uses the
  `recommend` helper
- **THEN** its render includes the same typed recommendation footnote
