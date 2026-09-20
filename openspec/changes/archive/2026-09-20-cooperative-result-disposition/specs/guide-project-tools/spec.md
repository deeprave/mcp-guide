## MODIFIED Requirements

### Requirement: Result Pattern Compliance

All project management tools SHALL return responses using the Result pattern.

#### Scenario: Unbound project error

- **WHEN** any tool requires a bound project and the session is unbound
- **THEN** it SHALL return the async no-project Result
- **AND** the result SHALL carry `agent/error` and guidance to call `set_project`
