# help-template-system Specification

## Purpose
Define template-based rendering of Guide command help and its context.
## Requirements
### Requirement: Template-Based Help Rendering
The system SHALL render individual command help using template-based rendering instead of programmatic string generation to enable richer formatting and workflow integration.

#### Scenario: Individual command help via template
- **WHEN** user requests help for a specific command (e.g., `:help status`)
- **THEN** render help content using template system with command metadata in context

#### Scenario: Template context population
- **WHEN** `get_command_help()` is called for a command
- **THEN** populate template context with command metadata (description, usage, examples, aliases)

### Requirement: Workflow-Aware Help Content
The system SHALL support workflow-aware help content through template conditionals when workflow management features are enabled.

#### Scenario: Phase-specific help content
- **WHEN** workflow management is enabled and user requests command help
- **THEN** include phase-specific guidance and workflow context in help display

#### Scenario: Conditional help sections
- **WHEN** rendering command help with template system
- **THEN** support conditional sections based on project flags and workflow state
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

### Requirement: Guided Onboarding Experience

The system SHALL provide a guided onboarding experience for project configuration.

#### Scenario: Initial onboarding guides user through setup
- **WHEN** a user begins onboarding for a project
- **THEN** the system guides them through relevant configuration choices
- **AND** it presents those choices in user-facing terms rather than requiring prior knowledge of internal configuration structures

#### Scenario: Onboarding supports later reconfiguration
- **WHEN** a user wants to revise project setup after initial onboarding
- **THEN** the same guided approach can be used to review and adjust existing configuration choices

#### Scenario: Onboarding summarizes current configuration before questioning
- **WHEN** onboarding begins
- **THEN** it summarizes the dimensions that are already configured before asking the first onboarding question

#### Scenario: Onboarding asks one question at a time
- **WHEN** onboarding needs user input for a remaining configuration dimension
- **THEN** it asks exactly one onboarding question at a time
- **AND** it waits for the user's response before asking the next onboarding question

#### Scenario: Clarifying questions are allowed during onboarding
- **WHEN** the user asks a clarifying question instead of answering the current onboarding question
- **THEN** onboarding answers the clarification
- **AND** resumes from the current onboarding dimension afterward

### Requirement: Project-Aware Guidance

The onboarding flow SHALL inspect existing guide configuration and project signals when possible, and ask the user when those signals are insufficient.

#### Scenario: Existing guide configuration informs onboarding choices
- **WHEN** onboarding begins
- **THEN** it inspects the current guide configuration before asking questions
- **AND** uses `guide://_project?verbose` as the primary source of current project/category state, including the `policies` category
- **AND** inspects project flags including `onboarded`, `workflow`, and `openspec`
- **AND** inspects available profiles before asking about language or framework profiles

#### Scenario: Project characteristics inform onboarding defaults
- **WHEN** the project contains recognizable language, framework, or toolchain signals
- **THEN** onboarding uses those signals to prioritize relevant setup questions
- **AND** proposes likely defaults when they can be inferred from the inspected state

#### Scenario: Fully configured dimensions are skipped silently
- **WHEN** a configuration dimension is already fully configured
- **THEN** onboarding does not ask the user about that dimension again

#### Scenario: Partially configured dimensions are revisited
- **WHEN** a configuration dimension is only partially configured
- **THEN** onboarding mentions the current state
- **AND** asks the user whether to confirm or adjust it

#### Scenario: Ambiguous or missing project context falls back to user questions
- **WHEN** project inspection or existing configuration is ambiguous or unavailable
- **THEN** onboarding asks the user for the missing information before applying configuration
