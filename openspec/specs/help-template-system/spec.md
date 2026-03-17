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

### Requirement: User Documentation

The system SHALL provide comprehensive user-facing documentation covering all major features and configuration options.

Documentation SHALL include:
- General usage and configuration guides
- Pattern syntax for categories and collections
- Output format documentation (MIME-multipart)
- Document management and frontmatter reference
- Template syntax and functions
- Template context reference
- Feature flags reference
- Commands and guide prompt usage

#### Scenario: User needs configuration guidance

- **WHEN** user wants to configure categories and collections
- **THEN** documentation provides clear examples and explanations
- **AND** documentation explains feature flags that affect behavior

#### Scenario: User needs pattern syntax guidance

- **WHEN** user wants to configure file patterns
- **THEN** documentation explains glob patterns (*, **, ?, [])
- **AND** documentation provides examples for common use cases
- **AND** documentation shows integration with categories and collections

#### Scenario: User needs output format guidance

- **WHEN** user wants to use MIME-multipart format
- **THEN** documentation explains when to use vs plain format
- **AND** documentation shows how to enable in tools
- **AND** documentation provides output structure examples

#### Scenario: User needs frontmatter reference

- **WHEN** user wants to add frontmatter to documents
- **THEN** documentation lists all supported keys and their formats
- **AND** documentation provides examples for common use cases

#### Scenario: User needs template help

- **WHEN** user wants to create or modify templates
- **THEN** documentation explains template syntax and conditionals
- **AND** documentation lists available functions and partials
- **AND** documentation links to authoritative Chevron/Mustache resources

#### Scenario: User needs template context reference

- **WHEN** user wants to use template variables
- **THEN** documentation lists all available context variables
- **AND** documentation organizes variables by group (system, agent, project, category, file)
- **AND** documentation explains template functions (format_date, truncate, highlight_code)
- **AND** documentation explains context hierarchy and precedence

#### Scenario: User needs feature flag reference

- **WHEN** user wants to enable or configure a feature
- **THEN** documentation explains each feature flag's purpose and format
- **AND** documentation provides configuration examples

#### Scenario: User needs command help

- **WHEN** user wants to use commands
- **THEN** documentation shows basic invocation format with one example
- **AND** documentation points to :help for discovering available commands

### Requirement: Documentation Standards

The system SHALL maintain consistent documentation standards across all user-facing documentation.

#### Scenario: Documentation format

- **WHEN** documentation is created
- **THEN** it uses Markdown format
- **AND** includes practical code examples
- **AND** provides working sample configurations
- **AND** links to external authoritative sources
- **AND** uses consistent heading structure

#### Scenario: Example requirements

- **WHEN** documenting a feature
- **THEN** at least 2 practical examples are provided
- **AND** examples are copy-pasteable
- **AND** both simple and advanced use cases are shown
- **AND** expected output is shown where relevant

#### Scenario: Cross-references

- **WHEN** documentation covers related topics
- **THEN** links between related sections are provided
- **AND** implementation files are referenced where appropriate
- **AND** troubleshooting sections are included
- **AND** "See Also" sections guide users to related content

### Requirement: Documentation Integration

The system SHALL integrate new documentation with existing documentation structure.

#### Scenario: README updates

- **WHEN** new documentation is added
- **THEN** README includes links to new documentation files
- **AND** feature overview references documentation
- **AND** documentation is easily discoverable

#### Scenario: Documentation consistency

- **WHEN** new documentation is added
- **THEN** existing overlapping content is updated
- **AND** consistency is maintained across all documentation
- **AND** outdated information is removed or updated

### Requirement: Documentation Validation

The system SHALL ensure documentation accuracy and usability.

#### Scenario: Content accuracy

- **WHEN** documentation is published
- **THEN** all examples are tested and working
- **AND** code samples match actual implementation
- **AND** all links are valid and current

#### Scenario: User experience

- **WHEN** users read documentation
- **THEN** content is accessible to new users
- **AND** complexity progresses from basic to advanced
- **AND** navigation between topics is clear
- **AND** content structure is searchable

### Requirement: Export Command Organization
The system SHALL organize export commands under `_commands/export/` directory structure.

#### Scenario: Export command structure
- **WHEN** export commands are discovered
- **THEN** they are located at `_commands/export/add.mustache`, `_commands/export/list.mustache`, `_commands/export/remove.mustache`
- **AND** `add.mustache` has alias 'export' for backward compatibility
- **AND** commands are accessible as `:export/add`, `:export/list`, `:export/remove`, and `:export`

### Requirement: Export List Command
The system SHALL provide an `:export/list` command that displays formatted export information.

#### Scenario: Display formatted exports
- **WHEN** `:export/list` command is invoked
- **THEN** agent is instructed to call `list_exports` tool
- **AND** result is formatted using `_system/_exports-format.mustache` template
- **AND** formatted output is displayed to user

#### Scenario: Command with filter
- **WHEN** `:export/list <glob>` command is invoked with a glob pattern
- **THEN** agent passes the glob to `list_exports` tool
- **AND** only matching exports are displayed

### Requirement: Export Remove Command
The system SHALL provide an `:export/remove` command that removes export tracking entries.

#### Scenario: Remove export tracking
- **WHEN** `:export/remove <expression> [pattern]` command is invoked
- **THEN** agent is instructed to call `remove_export` tool with the provided arguments
- **AND** success or error message is displayed

### Requirement: Export List Template
The system SHALL provide a `_system/_exports-format.mustache` template for formatting export lists.

#### Scenario: Format export list
- **WHEN** template receives export data array
- **THEN** each export is displayed with expression, pattern (if present), path, and timestamp
- **AND** stale exports are visually indicated with a warning marker
- **AND** empty list shows "No exports found" message

