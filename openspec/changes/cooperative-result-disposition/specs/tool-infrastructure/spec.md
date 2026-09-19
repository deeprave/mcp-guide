## ADDED Requirements

### Requirement: Result Disposition Field
`Result[T]` SHALL carry an optional `disposition` field identifying how the response should be treated, drawn from the disposition vocabulary defined by the `result-disposition` capability.

A `Result` SHALL prefer setting `disposition` over a prose `instruction` when the disposition alone conveys the required agent behavior. A prose `instruction` SHALL still be included alongside `disposition` when it carries information specific to that response that the disposition alone does not (for example, which arguments conflicted, or what value would succeed).

#### Scenario: Disposition set without a paired instruction
- **WHEN** a tool result's meaning is fully carried by its disposition
- **THEN** `Result.disposition` is set
- **AND** `Result.instruction` is absent

#### Scenario: Disposition set with response-specific instruction
- **WHEN** a tool result's disposition alone does not convey response-specific detail
- **THEN** `Result.disposition` is set
- **AND** `Result.instruction` carries only the detail the disposition does not
