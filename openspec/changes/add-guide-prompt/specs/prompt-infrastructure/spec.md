## ADDED Requirements

### Requirement: Direct Function Parameter Prompts
The system SHALL support MCP prompts using direct function parameters instead of complex argument classes.

#### Scenario: Variable argument support via fixed parameters
- **WHEN** prompts need variable arguments
- **THEN** use fixed optional parameters: arg1 through argF (15 total)
- **AND** parameters are Optional[str] = None
- **AND** parsing stops at first None value

#### Scenario: Argv-style argument parsing
- **WHEN** prompt function receives arguments
- **THEN** builds argv list: ["guide", arg1, arg2, ...]
- **AND** stops adding arguments at first None
- **AND** provides command-line style interface

#### Scenario: MCP argument compatibility
- **WHEN** MCP clients send space-separated arguments
- **THEN** each argument maps to individual function parameter
- **AND** no complex argument classes needed
- **AND** FastMCP handles parameter validation automatically

### Requirement: Prompt Decorator Infrastructure
The system SHALL provide prompt decorator infrastructure for FastMCP prompt registration.

#### Scenario: Direct function decoration
- **WHEN** prompt functions need registration
- **THEN** @mcp.prompt decorator handles FastMCP registration
- **AND** uses function signature for argument schema
- **AND** no custom argument classes required

#### Scenario: Prompt proxy pattern
- **WHEN** server initialization needs deferred prompt registration
- **THEN** prompt proxy pattern allows import-time decoration
- **AND** actual registration happens after server creation

### Requirement: Prompt Prefix Support
The system SHALL provide configurable prompt prefixes to avoid name collisions.

#### Scenario: Default prompt prefix behavior
- **WHEN** MCP_PROMPT_PREFIX environment variable is not set
- **THEN** prompts use no prefix (empty string)
- **AND** prompt names are registered as-is

#### Scenario: Custom prompt prefix
- **WHEN** MCP_PROMPT_PREFIX environment variable is set to "custom"
- **THEN** prompts are registered with "custom_" prefix
- **AND** "guide" prompt becomes "custom_guide"

#### Scenario: Prompt prefix configuration
- **WHEN** prompt decorator initializes
- **THEN** reads prefix from MCP_PROMPT_PREFIX environment variable
- **AND** defaults to empty string if not set
