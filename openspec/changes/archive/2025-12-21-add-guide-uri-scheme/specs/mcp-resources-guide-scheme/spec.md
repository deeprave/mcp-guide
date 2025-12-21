# Specification: MCP Resources - guide:// URI Scheme

## ADDED Requirements

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
