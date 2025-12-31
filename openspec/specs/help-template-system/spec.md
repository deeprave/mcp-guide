# help-template-system Specification

## Purpose
TBD - created by archiving change help-template-refactor. Update Purpose after archive.
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

### Requirement: Template Context Integration
The system SHALL integrate command help metadata into the template context system for consistent formatting and styling.

#### Scenario: Consistent help formatting
- **WHEN** rendering command help via template
- **THEN** use template styling system (h1, bold, etc.) for consistent appearance

#### Scenario: Help metadata availability
- **WHEN** template renders individual command help
- **THEN** have access to all command metadata (description, usage, examples, aliases, category)

