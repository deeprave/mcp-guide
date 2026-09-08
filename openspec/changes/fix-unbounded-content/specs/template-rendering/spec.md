## ADDED Requirements

### Requirement: Bounded template and partial content

The system SHALL check a template or partial source byte size against the global
`max-content-limit` before parsing or rendering it. It SHALL check each rendered
template before document formatting.

Policy-partial discovery and rendering SHALL receive the active global limits.
The server SHALL bound the aggregate rendered policy content before joining it
for the parent template.

#### Scenario: Oversized template source is rejected
- **WHEN** a selected template exceeds `max-content-limit`
- **THEN** it fails with `max_size_exceeded` before parsing or rendering

#### Scenario: Oversized rendered template is rejected
- **WHEN** rendering produces content exceeding `max-content-limit`
- **THEN** no oversized result is passed to document formatting
