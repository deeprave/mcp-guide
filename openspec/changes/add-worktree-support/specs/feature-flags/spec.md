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

## MODIFIED Requirements

### Requirement: Registered feature-flag normalisation

A flag with a registered validator or normaliser SHALL use that registration instead of the default scalar path. `path-documents` SHALL be stored only when explicitly configured; when absent, its documents directory is a runtime default. The template context's rendered `path.documents` value SHALL be an absolute path rooted at the project root and end with exactly one trailing slash.

#### Scenario: Registered path flag uses its normaliser

- **WHEN** `path-documents` is set to `"docs"`
- **THEN** its registered path normaliser determines the stored value

#### Scenario: Registered workflow flags use their own validation

- **WHEN** `workflow`, `workflow-file`, or `workflow-consent` is set through a feature-flag API
- **THEN** its registered validator and normaliser determine whether the value is accepted
- **AND** the generic default validator does not override that result

#### Scenario: Workflow-file value is resolved safely

- **WHEN** `workflow-file` is set to a supported path expression
- **THEN** its registered resolver substitutes supported project variables

#### Scenario: Default documents path is not stored

- **GIVEN** no `path-documents` value is configured
- **WHEN** Guide resolves and renders the documents directory
- **THEN** it SHALL use the runtime default without persisting a project flag
- **AND** the template context's rendered path SHALL be rooted at the project root and end with `/`
