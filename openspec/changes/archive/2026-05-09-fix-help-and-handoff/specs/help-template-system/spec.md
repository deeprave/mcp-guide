## MODIFIED Requirements

### Requirement: Help Template Enhancement

The system SHALL enhance the help template to support both general help listing and individual command help rendering.

#### Scenario: Unified help template
- **WHEN** help command is called without arguments
- **THEN** render general command listing as before

#### Scenario: Individual command help template
- **WHEN** help command is called with specific command argument
- **THEN** render detailed command help using template with populated context

#### Scenario: Help template uses command helper formatting
- **WHEN** command references are rendered in the help template
- **THEN** they are generated through the shared command helper family rather than hardcoded inline formatting
- **AND** the displayed command format follows the configured `format-command` behavior

#### Scenario: Other command templates use shared helper formatting
- **WHEN** command-oriented templates render guide command or resource references
- **AND** the shared helper family can express those references
- **THEN** they use the shared helper family instead of hardcoded command or resource syntax

#### Scenario: Prompt override affects prompt-style help rendering
- **WHEN** command references are rendered in prompt-style form in the help template
- **AND** `MCP_PROMPT_NAME` overrides the prompt name
- **THEN** the displayed prompt-style command references use the overridden prompt name

### Requirement: Template Context Integration

The template context SHALL expose template-friendly agent capability flags in addition to the existing agent identity fields.

#### Scenario: Consistent help formatting
- **WHEN** rendering command help via template
- **THEN** use template styling system (h1, bold, etc.) for consistent appearance

#### Scenario: Help metadata availability
- **WHEN** template renders individual command help
- **THEN** have access to all command metadata (description, usage, examples, aliases, category)

#### Scenario: Handoff capability is exposed
- **WHEN** command templates are rendered
- **THEN** the context includes `agent.has_handoff`
- **AND** it defaults to `false` unless explicitly enabled for a validated client

#### Scenario: Normalized-name membership flags are exposed
- **WHEN** command templates are rendered
- **THEN** the context includes `agent.is_<normalized-name>` boolean flags derived from the canonical normalized agent name
- **AND** templates can use these flags for light identity-specific wording

### Requirement: Handoff Command Flexibility

The `:handoff` command SHALL support explicit read and write workflows against a
user-supplied file path.

The command SHALL:
- Require a path argument naming the handoff file
- Require exactly one of `--read` or `--write`
- Reject invocations that specify both `--read` and `--write`
- Reject invocations that specify neither `--read` nor `--write`
- Instruct the agent explicitly whether it is reading existing context from the
  file or writing current context to it

#### Scenario: Write handoff file
- **WHEN** the user invokes `:handoff .context.md --write`
- **THEN** the rendered command instructs the agent to write the current context to `.context.md`
- **AND** it explains what information should be included

#### Scenario: Read handoff file
- **WHEN** the user invokes `:handoff .context.md --read`
- **THEN** the rendered command instructs the agent to read `.context.md` as input context
- **AND** it does not describe a write workflow

#### Scenario: Missing operation flag is invalid
- **WHEN** the user invokes `:handoff .context.md` without `--read` or `--write`
- **THEN** the command returns a validation-style error explaining that exactly one mode flag is required

#### Scenario: Both operation flags are invalid
- **WHEN** the user invokes `:handoff .context.md --read --write`
- **THEN** the command returns a validation-style error explaining that the flags are mutually exclusive

#### Scenario: Missing path is invalid
- **WHEN** the user invokes `:handoff --read` or `:handoff --write` without a file path
- **THEN** the command returns a validation-style error explaining that a handoff file path is required
