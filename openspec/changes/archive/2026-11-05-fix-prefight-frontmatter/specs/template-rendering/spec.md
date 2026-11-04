## MODIFIED Requirements

### Requirement: Elicitation-aware partial property collection

Before rendering an interactive skill or command entrypoint, the template system
SHALL collect only eligible parent and partial input declarations needed to resolve elicitation. It SHALL discard unrelated headers after resolving the state it needs and SHALL NOT merge preflight delivery properties into rendered output. It SHALL include frontmatter-only partials declared through the
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
- **AND** SHALL retain only its eligible elicitation contribution for input resolution

#### Scenario: Status skips setup partials

- **GIVEN** status declares `user/information`, agent information is available and workflow has a known phase
- **WHEN** status is delivered after preflight
- **THEN** skipped setup partials SHALL NOT contribute delivery metadata
- **AND** status SHALL retain `user/information`

#### Scenario: Rendered contributors remain authoritative

- **GIVEN** a parent and partial declare different disposition, instruction or cache settings
- **WHEN** the partial actually renders after input resolution
- **THEN** final metadata SHALL follow existing rendering composition rules
- **AND** preflight inspection SHALL NOT add another metadata contributor

### Requirement: Universal frontmatter template evaluation

The renderer SHALL treat only `instruction`, `description`, and `elicitation`
frontmatter values as Mustache templates. It SHALL use this same fixed whitelist
for rendered documents, commands, skills and partials. Interactive preflight SHALL evaluate only elicitation-related values needed for input resolution, using temporary supporting context as necessary; unrelated renderable headers SHALL NOT be evaluated as delivery fields during preflight. Structural metadata,
including `includes`, `cache`, and `type`, SHALL remain literal. Client-visible
source labels in frontmatter diagnostics SHALL be relative to the document root.

#### Scenario: Structural frontmatter remains literal

- **WHEN** a document, command, skill, or partial has structural frontmatter
  containing template syntax
- **THEN** Guide SHALL retain that value literally

#### Scenario: Interactive preflight uses the universal whitelist

- **WHEN** interactive preflight resolves parent or partial frontmatter
- **THEN** it SHALL evaluate only elicitation-related values needed for input resolution
- **AND** it SHALL use `requires-*` and `includes` for eligibility and discovery as needed
- **AND** it SHALL discard unrelated headers before returning preflight state
- **AND** original frontmatter SHALL remain available for independent rendering with resolved inputs

#### Scenario: Source-aware diagnostic

- **WHEN** elicitation composition reports a source path to an MCP client
- **THEN** that path SHALL be relative to the document root
