# Tool Infrastructure Capability

## ADDED Requirements

### Requirement: Tool Name Decoration
The system SHALL provide a decorator that adds configurable prefixes to tool names.

#### Scenario: Default prefix from environment
- **WHEN** ExtMcpToolDecorator is initialized without explicit prefix
- **THEN** the prefix is read from MCP_TOOL_PREFIX environment variable
- **AND** the default prefix is "guide_" if environment variable is not set

#### Scenario: Per-tool prefix override
- **WHEN** a tool is decorated with prefix parameter
- **THEN** the specified prefix is used instead of the default
- **AND** empty string disables prefix for that tool

#### Scenario: Tool name prefixing
- **WHEN** a tool is registered with the decorator
- **THEN** the final tool name is prefix + tool_name
- **AND** the tool is registered with FastMCP using the prefixed name

### Requirement: Automatic Tool Logging
The system SHALL automatically log all tool invocations and outcomes.

#### Scenario: Tool invocation logging
- **WHEN** a tool is called
- **THEN** a TRACE level log entry is created with "Tool called: {name}"
- **AND** the log entry is created before the tool executes

#### Scenario: Tool success logging (async)
- **WHEN** an async tool completes successfully
- **THEN** a TRACE level log entry is created with "Tool {name} completed successfully"

#### Scenario: Tool success logging (sync)
- **WHEN** a sync tool completes successfully
- **THEN** a DEBUG level log entry is created with "Tool {name} completed successfully"

#### Scenario: Tool failure logging
- **WHEN** a tool raises an exception
- **THEN** an ERROR level log entry is created with "Tool {name} failed: {error}"
- **AND** the exception is re-raised after logging

### Requirement: Result Pattern with Instruction Field
The system SHALL provide a Result[T] type for tool responses with instruction field.

#### Scenario: Success result
- **WHEN** a tool succeeds
- **THEN** Result contains optional value field with result data
- **AND** Result contains optional message field for user
- **AND** Result contains optional instruction field for agent

#### Scenario: Failure result
- **WHEN** a tool fails
- **THEN** Result contains error field with error message
- **AND** Result contains error_type field with error classification
- **AND** Result contains optional exception field with details
- **AND** Result contains optional message field for user
- **AND** Result contains optional instruction field for agent

#### Scenario: Instruction field usage
- **WHEN** Result includes instruction field
- **THEN** the instruction guides agent behavior
- **AND** the instruction is separate from user-facing message

### Requirement: Base Tool Arguments Model
The system SHALL provide a base Pydantic model for tool arguments.

#### Scenario: Base model inheritance
- **WHEN** a tool defines argument model
- **THEN** the model inherits from ToolArgs base class
- **AND** the model benefits from common validation patterns

#### Scenario: Unknown field rejection
- **WHEN** tool arguments include unknown fields
- **THEN** Pydantic validation rejects the arguments
- **AND** a clear error message is returned

### Requirement: Explicit Use Pattern
The system SHALL support explicit user consent for destructive operations.

#### Scenario: Literal type enforcement
- **WHEN** a destructive tool requires explicit consent
- **THEN** the tool argument includes Literal type field
- **AND** the field requires exact string match (e.g., "DELETE_DOCUMENT")
- **AND** Pydantic validation enforces the literal value

#### Scenario: Tool description warning
- **WHEN** a tool requires explicit consent
- **THEN** the tool description includes "REQUIRES EXPLICIT USER INSTRUCTION"
- **AND** the description explains the consent requirement
- **AND** the description warns against frivolous use

### Requirement: Auto-Generated Tool Schema
The system SHALL generate tool argument schema from Pydantic models.

#### Scenario: Schema generation
- **WHEN** a tool is registered with Pydantic argument model
- **THEN** the argument schema is automatically generated
- **AND** the schema includes field types and descriptions
- **AND** the schema is available to MCP clients

### Requirement: Tool Documentation Convention
The system SHALL enforce documentation conventions for tools.

#### Scenario: Undecorated name in documentation
- **WHEN** tool documentation is written
- **THEN** the undecorated tool name is used
- **AND** the prefix is not mentioned in documentation
- **AND** the prefix is treated as implementation detail

#### Scenario: Tool description format
- **WHEN** a tool is defined
- **THEN** the description is succinct and clear
- **AND** the description includes argument schema information
- **AND** the description marks explicit use requirements if applicable
