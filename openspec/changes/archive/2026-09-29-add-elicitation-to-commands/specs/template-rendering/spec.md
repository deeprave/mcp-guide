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

### Requirement: Universal frontmatter template evaluation

The renderer SHALL treat only `instruction`, `description`, and `elicitation`
frontmatter values as Mustache templates. It SHALL use this same fixed whitelist
for documents, commands, skills, partials, and interactive preflight; callers
SHALL NOT select a document-kind-specific rendering profile. Structural metadata,
including `includes`, `cache`, and `type`, SHALL remain literal. Client-visible
source labels in frontmatter diagnostics SHALL be relative to the document root.

#### Scenario: Structural frontmatter remains literal

- **WHEN** a document, command, skill, or partial has structural frontmatter
  containing template syntax
- **THEN** Guide SHALL retain that value literally

#### Scenario: Interactive preflight uses the universal whitelist

- **WHEN** interactive preflight resolves parent or partial frontmatter
- **THEN** it SHALL render only `instruction`, `description`, and `elicitation`
- **AND** it SHALL retain structural metadata literally before property
  composition

#### Scenario: Source-aware diagnostic

- **WHEN** elicitation composition reports a source path to an MCP client
- **THEN** that path SHALL be relative to the document root
