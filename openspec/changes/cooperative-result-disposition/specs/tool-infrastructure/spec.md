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

### Requirement: Result disposition is never fabricated
`Result.ok()` and `Result.failure()` SHALL NOT apply a blanket default disposition when none is given. A `Result`'s disposition SHALL be set only where the constructing call site has a genuinely known disposition for that content (a rendered document, skill, or command); otherwise it SHALL remain unset and be omitted from the serialized result.

#### Scenario: No disposition given, none fabricated
- **WHEN** `Result.ok()` or `Result.failure()` is called without an explicit `disposition`
- **THEN** the resulting `Result.disposition` is `None`
- **AND** the serialized result omits the `disposition` key entirely

#### Scenario: Category-specific defaults remain construction-time, not blanket
- **WHEN** a skill or command template renders with no explicit `type:` in its frontmatter
- **THEN** its resulting disposition is `agent/instruction`
- **AND** this default is determined by the rendering path for that content category, not by a `Result`-level fallback applied indiscriminately to every result
