## ADDED Requirements

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
