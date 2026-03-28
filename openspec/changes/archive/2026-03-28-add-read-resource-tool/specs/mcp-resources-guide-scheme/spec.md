## ADDED Requirements

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
