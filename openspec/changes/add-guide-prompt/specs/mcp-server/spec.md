## ADDED Requirements

### Requirement: Guide Prompt Support
The MCP server SHALL provide a `guide` prompt for direct content access without agent interpretation.

#### Scenario: Guide prompt with category
- **WHEN** user invokes `@guide category-name`
- **THEN** system calls get_content with category-name as argument
- **AND** returns content directly to user

#### Scenario: Guide prompt with pattern
- **WHEN** user invokes `@guide lang/python`
- **THEN** system calls get_content with "lang/python" as argument
- **AND** returns matching content

#### Scenario: Guide prompt without arguments
- **WHEN** user invokes `@guide` with no arguments
- **THEN** system handles gracefully with appropriate response
- **AND** does not error or crash

#### Scenario: Guide prompt with multiple arguments
- **WHEN** user invokes `@guide arg1 arg2 arg3`
- **THEN** system uses first argument (arg1) for MVP implementation
- **AND** reserves additional arguments for future use

### Requirement: Prompt Registration
The MCP server SHALL register prompts during server initialization alongside tools.

#### Scenario: Server startup with prompts
- **WHEN** MCP server initializes
- **THEN** guide prompt is registered with FastMCP
- **AND** prompt is available for client invocation
- **AND** prompt schema is provided to agents

#### Scenario: Prompt schema availability
- **WHEN** agent queries available prompts
- **THEN** guide prompt schema includes argument structure
- **AND** agents understand expected command and arguments format
