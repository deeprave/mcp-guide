# tool-infrastructure Specification

## Purpose
TBD - created by archiving change tool-conventions. Update Purpose after archive.
## Requirements
### Requirement: Result Pattern Implementation
The system SHALL provide a Result[T] generic type in mcp_core for tool responses.

#### Scenario: Success result creation
- **WHEN** a tool succeeds
- **THEN** Result.ok(value) creates success result with value
- **AND** success field is True
- **AND** optional message and instruction fields can be included

#### Scenario: Failure result creation
- **WHEN** a tool fails
- **THEN** Result.failure(error, error_type) creates failure result
- **AND** success field is False
- **AND** error and error_type fields are populated
- **AND** optional exception, message, and instruction fields can be included

#### Scenario: JSON serialization
- **WHEN** Result.to_json_str() is called
- **THEN** returns JSON string suitable for MCP tool response
- **AND** exception field is converted to exception_type and exception_message
- **AND** all optional fields are included if present

#### Scenario: Instruction field for agent guidance
- **WHEN** Result includes instruction field
- **THEN** instruction guides agent behavior (prevent remediation, suggest fixes, control modes)
- **AND** instruction is separate from user-facing message field

### Requirement: Tool Arguments Base Class
The system SHALL provide ToolArguments base class in mcp_core with tool collection support.

#### Scenario: Base model inheritance
- **WHEN** a tool defines argument model
- **THEN** model inherits from ToolArguments
- **AND** model benefits from common validation (extra="forbid", validate_assignment=True)

#### Scenario: Schema markdown generation
- **WHEN** ToolArguments.to_schema_markdown() is called
- **THEN** returns markdown-formatted argument schema
- **AND** includes argument names, types, required/optional status, and descriptions
- **AND** handles Literal types correctly

#### Scenario: Tool description building
- **WHEN** ToolArguments.build_tool_description(func) is called
- **THEN** combines function docstring with generated schema markdown
- **AND** returns complete tool description for MCP registration

### Requirement: Tool Collection Pattern
The system SHALL provide tool collection mechanism in ToolArguments for automatic discovery.

#### Scenario: Tool declaration
- **WHEN** @ToolArguments.declare decorator is applied to function
- **THEN** function is added to collection without wrapping
- **AND** function is returned unchanged for normal execution

#### Scenario: Collection retrieval
- **WHEN** ToolArguments.get_declared_tools() is called
- **THEN** returns dictionary of all declared tools
- **AND** clears collection to prevent double registration
- **AND** operation is thread-safe with asyncio lock

#### Scenario: Double registration prevention
- **WHEN** get_declared_tools() is called multiple times
- **THEN** second call returns empty dictionary
- **AND** tools are not registered twice with FastMCP

#### Scenario: Thread safety
- **WHEN** multiple coroutines access collection
- **THEN** asyncio lock protects _declared dictionary
- **AND** no race conditions occur during declare or get operations

### Requirement: Tool Name Decoration
The system SHALL provide ExtMcpToolDecorator in mcp_core that adds configurable prefixes.

#### Scenario: No default prefix
- **WHEN** ExtMcpToolDecorator is initialized without prefix parameter
- **THEN** reads prefix from MCP_TOOL_PREFIX environment variable
- **AND** uses empty string if environment variable not set

#### Scenario: Per-tool prefix override
- **WHEN** tool is decorated with prefix parameter
- **THEN** specified prefix is used instead of default
- **AND** empty string disables prefix for that tool

#### Scenario: Tool name prefixing
- **WHEN** tool is registered with decorator
- **THEN** final tool name is prefix + tool_name (if prefix not empty)
- **AND** tool is registered with FastMCP using final name

### Requirement: Automatic Tool Logging
The system SHALL automatically log all tool invocations via ExtMcpToolDecorator.

#### Scenario: Tool invocation logging
- **WHEN** tool is called
- **THEN** TRACE level log entry created with "Tool called: {name}"
- **AND** log entry created before tool executes

#### Scenario: Tool success logging (async)
- **WHEN** async tool completes successfully
- **THEN** TRACE level log entry created with "Tool {name} completed successfully"

#### Scenario: Tool success logging (sync)
- **WHEN** sync tool completes successfully
- **THEN** DEBUG level log entry created with "Tool {name} completed successfully"

#### Scenario: Tool failure logging
- **WHEN** tool raises exception
- **THEN** ERROR level log entry created with "Tool {name} failed: {error}"
- **AND** exception is re-raised after logging

### Requirement: Environment Configuration
The system SHALL configure MCP_TOOL_PREFIX early in mcp_guide startup.

#### Scenario: Default prefix configuration
- **WHEN** mcp_guide starts and MCP_TOOL_PREFIX not set
- **THEN** _configure_environment() sets MCP_TOOL_PREFIX="guide"
- **AND** configuration happens before server initialization

#### Scenario: User-provided prefix preserved
- **WHEN** mcp_guide starts and MCP_TOOL_PREFIX already set
- **THEN** existing value is preserved
- **AND** no override occurs

### Requirement: Tool Integration Pattern
The system SHALL integrate tool collection with FastMCP registration in server.py.

#### Scenario: Tool module import triggers collection
- **WHEN** tool modules are imported
- **THEN** @ToolArguments.declare decorators execute
- **AND** tools are added to collection

#### Scenario: Automatic registration with descriptions
- **WHEN** get_declared_tools() is called in server.py
- **THEN** for each tool, build_tool_description() generates complete description
- **AND** tool is registered with ExtMcpToolDecorator using generated description
- **AND** tool is registered with FastMCP

#### Scenario: Conditional example tool
- **WHEN** MCP_INCLUDE_EXAMPLE_TOOLS environment variable is "true"
- **THEN** tool_example module is imported
- **AND** example tools are included in registration
- **WHEN** environment variable is not "true"
- **THEN** tool_example module is not imported
- **AND** example tools are excluded

### Requirement: Explicit Use Pattern
The system SHALL support explicit user consent for destructive operations.

#### Scenario: Literal type enforcement
- **WHEN** destructive tool requires explicit consent
- **THEN** tool argument includes Literal type field
- **AND** field requires exact string match (e.g., "CREATE_DOCUMENT")
- **AND** Pydantic validation enforces literal value

#### Scenario: Tool description warning
- **WHEN** tool requires explicit consent
- **THEN** tool description includes "REQUIRES EXPLICIT USER INSTRUCTION"
- **AND** description explains consent requirement
- **AND** description warns against frivolous use

### Requirement: Tool Documentation Convention
The system SHALL enforce documentation conventions for tools.

#### Scenario: Undecorated name in documentation
- **WHEN** tool documentation is written
- **THEN** undecorated tool name is used
- **AND** prefix is not mentioned in documentation
- **AND** prefix is treated as implementation detail
- **AND** flag tools use explicit scope naming (project_flag vs feature_flag)

### Requirement: Project Flag Tool Naming
The system SHALL provide explicitly named tools for project flag operations.

#### Scenario: Project flag tool registration
- **WHEN** MCP server initializes
- **THEN** `set_project_flag` tool is registered for setting project flags
- **AND** `get_project_flag` tool is registered for getting project flags with resolution
- **AND** `list_project_flags` tool is registered for listing project flags

#### Scenario: Project flag resolution hierarchy
- **WHEN** `get_project_flag` or `list_project_flags` is called
- **THEN** project flags override global flags in resolution
- **AND** global flags provide defaults when project flags not set
- **AND** resolution hierarchy is preserved from original implementation

### Requirement: Global Flag Tool Naming
The system SHALL provide explicitly named tools for global flag operations.

#### Scenario: Global flag tool registration
- **WHEN** MCP server initializes
- **THEN** `set_feature_flag` tool is registered for setting global flags
- **AND** `get_feature_flag` tool is registered for getting global flags only
- **AND** `list_feature_flags` tool is registered for listing global flags only

#### Scenario: Global flag isolation
- **WHEN** global flag tools are called
- **THEN** operations work exclusively with `session.feature_flags()`
- **AND** no resolution hierarchy or project flag merging occurs
- **AND** operations are isolated to global scope only

### Requirement: Tool and Prompt Description Standards
The system SHALL enforce standardized 4-section documentation format for all MCP tools and prompts.

#### Scenario: Tool documentation format
- **WHEN** tool documentation is written
- **THEN** docstring includes Description section (≤50 chars first line if possible)
- **AND** docstring includes JSON Schema section with Pydantic-generated schema
- **AND** docstring includes Usage Instructions section with code examples
- **AND** docstring includes Concrete Examples section with real scenarios

#### Scenario: Prompt documentation format
- **WHEN** prompt documentation is written
- **THEN** docstring includes Description section (≤50 chars first line if possible)
- **AND** docstring includes Conceptual Schema section using *args interface
- **AND** docstring includes Usage Instructions section with @prompt_name syntax
- **AND** docstring includes Concrete Examples section with real invocations

#### Scenario: Field description completeness
- **WHEN** tool argument models are defined
- **THEN** all Pydantic fields include Field(description=...) parameters
- **AND** descriptions are clear, concise, and consistent with established patterns
- **AND** schema generation includes all field descriptions

#### Scenario: Documentation template references
- **WHEN** tool or prompt modules are created
- **THEN** module includes reference comment to appropriate README template
- **AND** tools reference src/mcp_guide/tools/README.md
- **AND** prompts reference src/mcp_guide/prompts/README.md

#### Scenario: Prompt varargs documentation
- **WHEN** prompt uses arg1...argF implementation pattern
- **THEN** documentation shows conceptual *args interface
- **AND** implementation details (arg1, arg2, etc.) are hidden from users
- **AND** examples use clean @prompt_name syntax

### Requirement: Direct Tool Invocation
The system SHALL allow prompts to call existing tools directly without decorator overhead.

#### Scenario: Tool function extraction
- **WHEN** prompt needs to call existing tool logic
- **THEN** tool implementation is accessible without decorator
- **AND** maintains same argument and context patterns

### Requirement: Tool Description Standard for AI Agents
The system SHALL provide a standardized format for tool descriptions that enables AI agents to correctly understand and invoke tools without trial-and-error.

#### Scenario: Description structure
- **WHEN** a tool is documented
- **THEN** description includes four sections in order:
  1. Full description of purpose and use cases (markdown format)
  2. JSON Schema for arguments (code fence with type annotation)
  3. General usage instructions (marked as code)
  4. Concrete examples with explanations (marked as code)
- **AND** each section is clearly labeled

#### Scenario: Template availability
- **WHEN** developer creates new tool
- **THEN** `src/mcp_guide/tools/README.md` provides complete template
- **AND** template shows proper formatting for all four sections
- **AND** template includes example of Pydantic Field descriptions

#### Scenario: Tool module references
- **WHEN** tool module is created or updated
- **THEN** module includes comment pointing to README template
- **AND** comment appears near tool definition

#### Scenario: Complete field descriptions
- **WHEN** tool argument model is defined with Pydantic
- **THEN** every field includes `Field(description="...")` parameter
- **AND** description explains field purpose and valid values
- **AND** generated JSON Schema includes all field descriptions

#### Scenario: Schema presentation
- **WHEN** JSON Schema is included in tool description
- **THEN** schema is in code fence with appropriate type label
- **AND** schema shows complete Pydantic-generated structure
- **AND** schema is not open to interpretation

#### Scenario: Usage instructions clarity
- **WHEN** usage instructions are provided
- **THEN** instructions are marked as code for clarity
- **AND** instructions explain general patterns for tool invocation

#### Scenario: Example completeness
- **WHEN** examples are provided
- **THEN** examples include concrete values (not placeholders)
- **AND** each example includes explanation of what it demonstrates
- **AND** examples are marked as code

### Requirement: Slash Syntax Content Retrieval
The system SHALL support `category/pattern` syntax as shorthand for two-parameter content retrieval.

#### Scenario: Basic slash syntax
- **WHEN** `get_content("lang/python")` is called
- **THEN** it SHALL be equivalent to `get_content("lang", "python")`
- **AND** the category is "lang" and pattern is "python"

### Requirement: Multi-Pattern Category Support
The system SHALL support multiple patterns within a single category using `+` separator.

#### Scenario: Multiple patterns with plus separator
- **WHEN** `get_content("lang/python+java+rust")` is called
- **THEN** content matching ANY of the patterns SHALL be retrieved
- **AND** results from all matching patterns SHALL be aggregated

### Requirement: Multi-Category Expression Support
The system SHALL support comma-separated expressions for retrieving content from multiple categories.

#### Scenario: Multi-category comma separation
- **WHEN** `get_content("lang/python,docs/api,guidelines")` is called
- **THEN** content SHALL be retrieved from all three specifications
- **AND** results SHALL be aggregated in order

