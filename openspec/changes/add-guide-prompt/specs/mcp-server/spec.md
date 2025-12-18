## ADDED Requirements

### Requirement: Guide Prompt Support
The MCP server SHALL provide a `guide` prompt for direct content access without agent interpretation.

#### Scenario: Guide prompt with single argument
- **WHEN** user invokes `@guide category-name`
- **THEN** system calls get_content with category-name as argument
- **AND** returns content directly to user

#### Scenario: Guide prompt with multiple arguments
- **WHEN** user invokes `@guide lang/python advanced tutorial`
- **THEN** system processes first argument "lang/python" for MVP
- **AND** builds argv list: ["guide", "lang/python", "advanced", "tutorial"]
- **AND** reserves additional arguments for future click processing

#### Scenario: Guide prompt without arguments
- **WHEN** user invokes `@guide` with no arguments
- **THEN** system returns help message with usage examples
- **AND** does not error or crash

#### Scenario: Guide prompt argument parsing
- **WHEN** MCP client sends space-separated arguments
- **THEN** each argument maps to arg1, arg2, ..., argF parameters
- **AND** parsing stops at first None parameter
- **AND** builds clean argv list for processing

### Requirement: Prompt Registration
The MCP server SHALL register prompts during server initialization alongside tools.

#### Scenario: Server startup with prompts
- **WHEN** MCP server initializes
- **THEN** guide prompt is registered with FastMCP
- **AND** prompt uses direct function parameters (arg1-argF)
- **AND** prompt is available for client invocation

#### Scenario: Prompt schema availability
- **WHEN** agent queries available prompts
- **THEN** guide prompt schema shows 15 optional string parameters
- **AND** agents understand space-separated argument mapping
