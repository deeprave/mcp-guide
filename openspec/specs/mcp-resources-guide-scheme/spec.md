# mcp-resources-guide-scheme Specification

## Purpose
TBD - created by archiving change add-guide-uri-scheme. Update Purpose after archive.
## Requirements
### Requirement: URI Scheme Declaration

The MCP server SHALL support the guide:// URI scheme for accessing guide content through MCP resources protocol.

#### Scenario: Resource template advertised
- **WHEN** client calls `resources/list`
- **THEN** response includes resourceTemplates with guide:// URI pattern

### Requirement: URI Pattern Structure

The guide:// URI scheme SHALL support the following pattern:

- `guide://{collection}[/{document}]` - Collection/category content with optional document pattern

The URI SHALL be parsed as:
- Collection/category name: path segment after scheme (required)
- Document pattern: optional second path segment (defaults to empty if omitted)

#### Scenario: Collection access
- **WHEN** client reads `guide://lang`
- **THEN** server returns content from collection/category "lang" using default patterns (document parameter is empty)

#### Scenario: Collection with document access
- **WHEN** client reads `guide://lang/python`
- **THEN** server returns content from collection/category "lang" matching pattern "python"

### Requirement: Resource Handler Registration

The MCP server SHALL register a resource handler for the guide:// URI template pattern.

The handler SHALL be registered using FastMCP resource decorator with URI template `guide://{collection}/{document}`.

#### Scenario: Handler registration
- **WHEN** server initializes
- **THEN** guide:// resource handler is registered with MCP server

### Requirement: Content Delegation

The resource handler SHALL delegate to `internal_get_content` function for content retrieval.

URI parameters SHALL be mapped to ContentArgs:
- collection → category_or_collection
- document → pattern (None if empty)

#### Scenario: Content delegation
- **WHEN** guide:// URI is accessed
- **THEN** handler calls `internal_get_content` with appropriate ContentArgs

#### Scenario: Parameter mapping
- **WHEN** URI is `guide://docs/readme`
- **THEN** ContentArgs has category_or_collection="docs" and pattern="readme"

#### Scenario: Empty document parameter
- **WHEN** URI is `guide://docs`
- **THEN** ContentArgs has category_or_collection="docs" and pattern=None

### Requirement: Response Format

Successful content retrieval SHALL return plain text content.

Failed content retrieval SHALL return error message as plain text.

#### Scenario: Successful retrieval
- **WHEN** content is found
- **THEN** handler returns content text as string

#### Scenario: Content error
- **WHEN** content retrieval fails
- **THEN** handler returns error message as string

### Requirement: Error Handling

The resource handler SHALL handle exceptions gracefully.

Unexpected exceptions SHALL be caught and returned as error messages.

#### Scenario: Exception handling
- **WHEN** unexpected exception occurs
- **THEN** handler returns "Unexpected error: {message}" string

### Requirement: Command URI Pattern

The guide:// URI scheme SHALL support command execution using underscore-prefixed paths:

- `guide://_command` - Command with no arguments
- `guide://_command/arg1/arg2` - Command with positional arguments
- `guide://_command?kwarg=value` - Command with keyword arguments
- `guide://_command/arg1?kwarg=value` - Command with both positional and keyword arguments

The underscore prefix in the netloc SHALL distinguish command URIs from content URIs.

#### Scenario: Simple command
- **WHEN** client reads `guide://_project`
- **THEN** server executes `project` command with no arguments

#### Scenario: Command with positional args
- **WHEN** client reads `guide://_perm/write-add/docs/`
- **THEN** server executes `perm/write-add` command with args `["docs/"]`

#### Scenario: Command with keyword args
- **WHEN** client reads `guide://_status?verbose=true`
- **THEN** server executes `status` command with kwargs `{"verbose": True}`

#### Scenario: Command with both arg types
- **WHEN** client reads `guide://_openspec/list?verbose=true`
- **THEN** server executes `openspec/list` command with kwargs `{"verbose": True}`

### Requirement: Command URI Resource Template

The MCP server SHALL advertise a separate resource template for command URIs.

The resource template SHALL use pattern `guide://_{command}` to explicitly indicate underscore prefix.

The server SHALL register both content and command resource templates in `resources/list`.

#### Scenario: Command template advertised
- **WHEN** client calls `resources/list`
- **THEN** response includes resource template with URI pattern `guide://_{command}`

#### Scenario: Both templates advertised
- **WHEN** client calls `resources/list`
- **THEN** response includes both `guide://{collection}/{document}` and `guide://_{command}` templates

### Requirement: Command Path Resolution

The URI parser SHALL use the command cache to resolve command paths.

The parser SHALL match the longest valid command path from the URI, with remaining path segments becoming positional arguments.

The command cache SHALL be accessed via `discover_commands()` which caches command metadata from the `_commands` category.

#### Scenario: Multi-segment command path
- **WHEN** URI is `guide://_perm/write-add/docs/`
- **AND** command cache contains `perm/write-add`
- **THEN** command path is `perm/write-add` and args are `["docs/"]`

#### Scenario: Single-segment command with no args
- **WHEN** URI is `guide://_project`
- **AND** command cache contains `project`
- **THEN** command path is `project` and args are `[]`

### Requirement: Query Parameter Parsing

The URI parser SHALL parse query parameters as keyword arguments.

Boolean flags without values SHALL default to True.
Boolean flags with explicit values SHALL parse "true" as True and "false" as False.
Non-boolean values SHALL be passed as strings.

#### Scenario: Boolean flag without value
- **WHEN** URI is `guide://_status?verbose`
- **THEN** kwargs are `{"verbose": True}`

#### Scenario: Boolean flag with true value
- **WHEN** URI is `guide://_status?verbose=true`
- **THEN** kwargs are `{"verbose": True}`

#### Scenario: Boolean flag with false value
- **WHEN** URI is `guide://_status?verbose=false`
- **THEN** kwargs are `{"verbose": False}`

#### Scenario: String value
- **WHEN** URI is `guide://_perm/write-add?path=docs/`
- **THEN** kwargs are `{"path": "docs/"}`

#### Scenario: Multiple query params
- **WHEN** URI is `guide://_openspec/show?change=enable-codex-integration&verbose=true`
- **THEN** kwargs are `{"change": "enable-codex-integration", "verbose": True}`

### Requirement: Command Execution Delegation

The resource handler SHALL detect command URIs by checking for underscore prefix in netloc.

Command URIs SHALL be routed to the existing command handler infrastructure.

The handler SHALL pass parsed command path, positional args, and keyword args to `handle_command()`.

#### Scenario: Command URI detection
- **WHEN** URI netloc starts with underscore
- **THEN** URI is classified as command URI

#### Scenario: Content URI detection
- **WHEN** URI netloc does not start with underscore
- **THEN** URI is classified as content URI

#### Scenario: Command delegation
- **WHEN** command URI is processed
- **THEN** handler calls `handle_command()` with parsed command path, args, and kwargs

### Requirement: Command Response Format

Command execution SHALL return output as-is from the command handler.

MCP instructions in command output SHALL be preserved.

#### Scenario: Command output returned
- **WHEN** command executes successfully
- **THEN** handler returns command output text

#### Scenario: MCP instructions preserved
- **WHEN** command output contains MCP instructions
- **THEN** instructions are included in response

### Requirement: Backward Compatibility

Existing content URI pattern `guide://collection/document` SHALL continue to work unchanged.

Content URIs SHALL be distinguished from command URIs by absence of underscore prefix.

#### Scenario: Content URI still works
- **WHEN** client reads `guide://docs/readme`
- **THEN** server returns content from docs collection matching readme pattern

#### Scenario: No collision with commands
- **WHEN** client reads `guide://docs`
- **AND** no underscore prefix present
- **THEN** server treats as content URI, not command

### Requirement: Command URI Error Handling

Invalid command paths SHALL return error messages.

Command execution failures SHALL return error messages.

#### Scenario: Invalid command
- **WHEN** URI is `guide://_nonexistent`
- **THEN** handler returns "Command not found: nonexistent" error

#### Scenario: Command execution error
- **WHEN** command execution fails
- **THEN** handler returns error message from command handler

### Requirement: Read Resource Tool

The MCP server SHALL provide a `read_resource` tool that accepts a `guide://` URI and returns the corresponding resource content or command output.

The tool SHALL accept only URIs with the `guide://` scheme. All other schemes SHALL be rejected with an error.

#### Scenario: Read collection content
- **WHEN** agent calls `read_resource` with URI `guide://docs`
- **THEN** tool returns content from collection/category "docs"

#### Scenario: Read specific document
- **WHEN** agent calls `read_resource` with URI `guide://docs/readme`
- **THEN** tool returns content matching pattern "readme" from "docs"

#### Scenario: Invalid URI scheme
- **WHEN** agent calls `read_resource` with a non-guide:// URI
- **THEN** tool returns an error indicating only guide:// URIs are supported

#### Scenario: Content not found
- **WHEN** agent calls `read_resource` with a valid URI but no matching content
- **THEN** tool returns an appropriate error message

### Requirement: Command URI Support

The `read_resource` tool SHALL support command execution via underscore-prefixed paths in the URI.

The underscore prefix in the URI path SHALL distinguish command URIs from content URIs.

#### Scenario: Simple command
- **WHEN** agent calls `read_resource` with URI `guide://_project`
- **THEN** tool executes `project` command with no arguments

#### Scenario: Command with positional args
- **WHEN** agent calls `read_resource` with URI `guide://_perm/write-add/docs/`
- **THEN** tool executes `perm/write-add` command with args `["docs"]`

#### Scenario: Command with keyword args
- **WHEN** agent calls `read_resource` with URI `guide://_status?verbose=true`
- **THEN** tool executes `status` command with kwargs `{"verbose": True}`

#### Scenario: Command with both arg types
- **WHEN** agent calls `read_resource` with URI `guide://_openspec/list?verbose=true`
- **THEN** tool executes `openspec/list` command with kwargs `{"verbose": True}`

#### Scenario: Invalid command
- **WHEN** agent calls `read_resource` with URI `guide://_nonexistent`
- **THEN** tool returns "Command not found" error

### Requirement: URI Parser Module

The server SHALL provide a URI parser that extracts content or command components from `guide://` URIs.

The parser SHALL use the command cache to resolve command paths via longest-match against known commands.

Query parameters SHALL be parsed as keyword arguments with boolean inference (`?verbose` → True, `?verbose=false` → False).

#### Scenario: Content URI parsing
- **WHEN** URI is `guide://docs/readme`
- **THEN** parser returns expression="docs", pattern="readme", is_command=False

#### Scenario: Command URI parsing
- **WHEN** URI is `guide://_openspec/list?verbose=true`
- **AND** command cache contains `openspec/list`
- **THEN** parser returns command_path="openspec/list", args=[], kwargs={"verbose": True}, is_command=True

#### Scenario: Command path resolution with args
- **WHEN** URI is `guide://_perm/write-add/docs/`
- **AND** command cache contains `perm/write-add`
- **THEN** parser returns command_path="perm/write-add", args=["docs"], is_command=True

#### Scenario: Boolean query param without value
- **WHEN** URI query contains `?verbose`
- **THEN** kwargs contains `{"verbose": True}`

### Requirement: Collection Underscore Validation

Collection names SHALL NOT start with an underscore prefix.

This prevents collision between user-created collections and command URIs.

#### Scenario: Reject underscore-prefixed collection name
- **WHEN** user attempts to create a collection named `_system`
- **THEN** server returns validation error

#### Scenario: Reject underscore-prefixed collection rename
- **WHEN** user attempts to rename a collection to `_reserved`
- **THEN** server returns validation error

