## ADDED Requirements

### Requirement: PromptArguments Protocol
The system SHALL provide a PromptArguments protocol in mcp_core for prompt argument validation.

#### Scenario: PromptArguments protocol definition
- **WHEN** prompt arguments need type safety
- **THEN** PromptArguments protocol provides base interface
- **AND** follows same patterns as ToolArguments

#### Scenario: GuidePromptArguments implementation
- **WHEN** guide prompt needs argument structure
- **THEN** GuidePromptArguments implements PromptArguments
- **AND** provides command: Optional[str] field
- **AND** provides arguments: List[str] field

#### Scenario: Prompt schema generation
- **WHEN** prompt decorator processes PromptArguments class
- **THEN** automatically generates JSON schema for FastMCP
- **AND** agents receive schema information for proper invocation

### Requirement: Prompt Decorator Infrastructure
The system SHALL provide prompt decorator infrastructure for FastMCP prompt registration.

#### Scenario: Prompt decorator creation
- **WHEN** prompt functions need registration
- **THEN** prompt decorator handles FastMCP registration
- **AND** supports argument validation and schema generation

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
