## ADDED Requirements

### Requirement: Elicitation-aware partial property collection

Before rendering an interactive skill or command entrypoint, the template system
SHALL collect eligible parent and partial frontmatter properties needed to resolve
elicitation. It SHALL include frontmatter-only partials declared through the
existing parent partial list, while retaining existing output interpolation rules.

#### Scenario: Collect properties before interactive rendering

- **WHEN** an interactive command or skill has parent or eligible partial
  elicitation frontmatter
- **THEN** the renderer SHALL make the composed declarations available before
  rendering output
- **AND** SHALL render output only after the interaction has resolved the
  applicable required values

#### Scenario: Do not interpolate a property-only partial

- **WHEN** a listed partial contributes frontmatter properties but is not
  referenced by a Mustache partial tag
- **THEN** the renderer SHALL not append or otherwise interpolate that partial's
  body content
- **AND** SHALL retain its eligible frontmatter contribution

### Requirement: Selective interactive frontmatter evaluation

The renderer SHALL retain existing frontmatter semantics for templates without interactive
preflight. Interactive command and selected-skill preflight MAY render only the parsed
frontmatter values required for elicitation and delivery-property composition, including
`elicitation`, `cache`, and `type`. It SHALL not enable generic all-field rendering for ordinary
template delivery. Client-visible source labels in frontmatter diagnostics SHALL be relative to
the document root.

#### Scenario: Ordinary template retains structural literal frontmatter

- **WHEN** a template without interactive preflight has a structural frontmatter value containing
  template syntax
- **THEN** Guide SHALL retain the existing ordinary rendering behaviour for that value

#### Scenario: Interactive partial delivery property uses parent context

- **WHEN** a listed interactive partial declares a templated `cache` or `type` value using a
  parent frontmatter variable
- **THEN** Guide SHALL resolve that property with the parent context before composing delivery
  properties

#### Scenario: Source-aware diagnostic

- **WHEN** elicitation composition reports a source path to an MCP client
- **THEN** that path SHALL be relative to the document root
