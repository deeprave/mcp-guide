## MODIFIED Requirements

### Requirement: Async factory for no-project result

The system SHALL provide an async `make_no_project_result()` factory that returns an `agent/error` Result. It SHALL render `_system/_project-root` without a session when possible, cache that rendered instruction per process, and fall back to `INSTRUCTION_NO_PROJECT` if rendering is unavailable.

#### Scenario: Rendering failure falls back to static instruction

- **WHEN** no-project guidance cannot be rendered
- **THEN** the factory SHALL return the static fallback instruction
- **AND** the unbound-project response SHALL remain a Result

#### Scenario: Unbound session returns rendered instruction

- **WHEN** a tool requiring a project is called while unbound
- **THEN** the Result SHALL use rendered no-project guidance when available

#### Scenario: No session falls back to static instruction

- **WHEN** no runtime is available for rendering
- **THEN** the Result SHALL use `INSTRUCTION_NO_PROJECT`

#### Scenario: Bound session is unaffected

- **WHEN** a tool requiring a project has a bound session
- **THEN** normal tool execution SHALL continue
