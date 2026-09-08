## ADDED Requirements

### Requirement: Bounded Template and Partial Input

The system SHALL check the byte size of every template and partial before reading
or parsing its body. A template or partial larger than the configured template
source limit SHALL fail with `max_size_exceeded` and SHALL NOT be parsed or
rendered.

For one template render, the system SHALL also limit resolved partial input to 32
partials and 1 MiB of aggregate UTF-8 source bytes. This includes frontmatter
includes and policy partials; cached content remains subject to the same limits.

#### Scenario: Oversized template is rejected before parsing
- **WHEN** a selected template is larger than the configured template source limit
- **THEN** rendering fails with `max_size_exceeded`
- **AND** the template body is not loaded for frontmatter processing or Mustache rendering

#### Scenario: Partial expansion exceeds the aggregate input budget
- **WHEN** a template resolves more than 32 partials or more than 1 MiB of aggregate partial source bytes
- **THEN** rendering fails with `max_size_exceeded`
- **AND** it does not render a partial result

### Requirement: Bounded Template Expansion

The system SHALL enforce the configured per-template rendered-output byte limit
while expanding Mustache content. A template expansion that would exceed the limit
SHALL stop and fail with `max_size_exceeded`; it SHALL NOT first construct the
full oversized rendered string in memory.

Rendered template bytes SHALL also count toward the enclosing content request's
aggregate response-byte limit.

#### Scenario: Repeated Mustache expansion exceeds the output limit
- **WHEN** template variables or sections would expand a template beyond its rendered-output byte limit
- **THEN** rendering stops with `max_size_exceeded`
- **AND** no oversized rendered value is passed to content formatting
