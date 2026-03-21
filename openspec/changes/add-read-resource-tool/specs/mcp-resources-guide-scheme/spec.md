## ADDED Requirements

### Requirement: Read Resource Tool

The MCP server SHALL provide a `read_resource` tool that accepts a `guide://` URI and returns the corresponding resource content.

The tool SHALL parse the URI to extract collection and optional document components, and delegate to the existing content retrieval infrastructure.

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
