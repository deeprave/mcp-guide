## MODIFIED Requirements

### Requirement: Frontmatter-only elicitation partials

The system SHALL allow a frontmatter partial to contribute elicitation declarations without emitting body content. A partial named in the parent's frontmatter partial list SHALL be processed for eligible elicitation declarations even when it is not interpolated through a Mustache partial tag. Preflight SHALL NOT carry its delivery headers into the response. Its body SHALL NOT be
included in rendered output unless the parent also interpolates it through the
existing partial mechanism.

#### Scenario: Property-only partial supplies a form

- **WHEN** a command or skill lists a partial containing only frontmatter that
  declares an elicitation form
- **THEN** Guide SHALL process and combine that form
- **AND** SHALL not add body content from that partial to the rendered entrypoint

#### Scenario: Property-only partial has no form

- **WHEN** a parent lists a frontmatter-only partial that contributes no
  elicitation declaration
- **THEN** Guide SHALL contribute no elicitation or response metadata from preflight inspection of that partial
- **AND** SHALL not change the rendered body solely because the partial was listed

#### Scenario: Interactive partial cannot be loaded

- **WHEN** an entrypoint cannot load one of its listed property contributors
- **THEN** Guide SHALL log a source-aware warning
- **AND** SHALL continue without that contributor
- **AND** SHALL NOT make partial availability a client-facing elicitation failure

#### Scenario: Malformed includes declaration

- **WHEN** an entrypoint's `includes` declaration is present but is not a list of strings
- **THEN** Guide SHALL log a source-aware warning
- **AND** SHALL continue as if it had no preflight partial contributors
- **AND** an absent `includes` declaration SHALL remain valid and produce no warning

#### Scenario: Form-only delivery headers are discarded

- **GIVEN** a command or skill lists an eligible form-only partial declaring `type`, `instruction`, or `cache`
- **WHEN** its form is resolved and the partial is not rendered
- **THEN** the resolved inputs SHALL be available to rendering
- **AND** none of those delivery headers SHALL affect response metadata
