## MODIFIED Requirements

### Requirement: Content Accessor Lambda

The system SHALL provide a `resource` template lambda that renders content references in a configurable format.

The resource lambda SHALL:
- Accept an expression string and render it as a content reference
- Use a feature flag named `format-resource`, exposed by `FLAG_RESOURCE`
- Default to `guide://expression` URI format when `format-resource` is `false` or unset
- Render as `get_content("expression")` when `format-resource` is `true`
- Be registered in the template context as `resource`
- Use a named feature-flag constant and registered boolean validator/normaliser path rather than ad hoc string-only lookup
- Use URI rendering as the universal default when `format-resource` is unset

#### Scenario: Default rendering (guide:// URI)
- **WHEN** `{{#resource}}guidelines{{/resource}}` is rendered
- **AND** `format-resource` is `false` or unset
- **THEN** output is `guide://guidelines`

#### Scenario: Tool rendering
- **WHEN** `{{#resource}}guidelines{{/resource}}` is rendered
- **AND** `format-resource` is `true`
- **THEN** output is `get_content("guidelines")`

### Requirement: Command Accessor Lambda

The system SHALL provide a template helper family for rendering command references
in a configurable format.

The command helper family SHALL:
- Be registered in template context as `command`, `command-args`, `command-flags`,
  and `command-alias`
- Support composing a command reference from a base command plus adjacent
  arguments, flags, and aliases in the same template region
- Support a `format-command` feature flag, exposed by `FLAG_COMMAND`, that controls output format
- Render as a `guide://_...` command URI when `format-command` is `false` or unset
- Render as a tool-oriented command reference when `format-command` is `true`
- Use URI rendering as the universal default when `format-command` is unset

URI rendering SHALL follow the command-resource shape:
- base form: `guide://_{command}`
- positional args appended as path segments
- flags rendered as query parameters

Tool-oriented rendering SHALL follow the guide tool/reference shape:
- base form uses the effective prompt name and current prompt prefix when prompt-style output is required
- positional args rendered space-separated after the command
- flags rendered as `--name=value` or `--name` for truthy valueless flags

#### Scenario: URI rendering for explicit flag
- **WHEN** `{{#command}}doit{{/command}}{{#command-args}}now{{/command-args}}{{#command-flags}}verbose=true,from=hello{{/command-flags}}` is rendered
- **AND** `format-command` is `false` or unset
- **THEN** the output is a `guide://_doit/...` URI
- **AND** positional args are encoded as URI path segments
- **AND** flags are encoded as URI query parameters

#### Scenario: Tool-oriented rendering for explicit flag
- **WHEN** `{{#command}}doit{{/command}}{{#command-args}}now{{/command-args}}{{#command-flags}}verbose=true,from=hello{{/command-flags}}` is rendered
- **AND** `format-command` is `true`
- **THEN** the output is a tool-oriented command reference
- **AND** positional args are rendered after the command name
- **AND** flags are rendered with `--` syntax

#### Scenario: Unset command format chooses URI form
- **WHEN** `format-command` is unset
- **THEN** `{{#command}}status{{/command}}` renders as a `guide://_status` URI

#### Scenario: Adjacent helper sections compose one command reference
- **WHEN** `command`, `command-args`, `command-flags`, or `command-alias` helper sections are used adjacently in a template
- **THEN** they contribute to the same command reference rather than rendering independently

#### Scenario: Aliases can be rendered alongside command reference
- **WHEN** a template uses `{{#command}}help{{/command}}{{#command-alias}}?,h{{/command-alias}}`
- **THEN** the helper family provides access to the aliases for rendering
- **AND** alias formatting remains consistent with the selected `format-command` mode

#### Scenario: Shared helpers replace hardcoded template references
- **WHEN** an existing template renders guide command or resource references
- **AND** the shared `command` / `resource` helper family can express that reference
- **THEN** the template uses the shared helper family instead of hardcoded `@guide`, `/guide`, or ad hoc resource formatting

### Requirement: Prompt name override

The system SHALL allow the registered guide prompt name to be overridden by
environment variable.

The prompt naming behavior SHALL:
- Default to prompt name `guide` when no override is set
- Use `MCP_PROMPT_NAME` as the override source when present
- Apply the overridden name consistently to prompt registration and prompt-style
  command rendering
- Not affect `guide://` URI rendering, which remains on the `guide://` scheme

#### Scenario: Default prompt name remains guide
- **WHEN** `MCP_PROMPT_NAME` is unset
- **THEN** prompt registration uses `guide`

#### Scenario: Prompt name overridden by environment
- **WHEN** `MCP_PROMPT_NAME=g`
- **THEN** prompt registration uses `g`
- **AND** prompt-style command rendering uses `@g` or `/g` according to the client prefix

#### Scenario: URI rendering is unaffected by prompt override
- **WHEN** `MCP_PROMPT_NAME` is set
- **AND** a template renders `{{#command}}status{{/command}}` in URI mode
- **THEN** the output remains `guide://_status`

### Requirement: Prompt name variable

The template support system SHALL expose the effective prompt name as a simple
template variable for compatibility and edge-case templates.

#### Scenario: Prompt variable rendering
- **WHEN** a template renders `{{prompt}}`
- **THEN** the output is the effective prompt name
- **AND** if `MCP_PROMPT_NAME` is set, `{{prompt}}` reflects that override
- **AND** command helper templates remain the preferred mechanism for command references

### Requirement: Static documentation command format

Static documentation SHALL use `guide://` URI syntax as the canonical form for
guide command and resource references.

#### Scenario: Static docs prefer URI syntax
- **WHEN** static documentation includes guide command examples or resource references
- **THEN** the primary documented syntax is `guide://...`
- **AND** prompt-style syntax may appear only as a note or reminder, not as the canonical form
- **AND** static docs do not rely on a specific prompt prefix or fixed prompt name
