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
