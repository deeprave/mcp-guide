# Specification: MCP Resources - guide:// URI Scheme

## ADDED Requirements

### Requirement: URI Scheme Declaration

The MCP server SHALL support the guide:// URI scheme for accessing guide content through MCP resources protocol.

#### Scenario: Resource discovery
- **WHEN** client calls `resources/list`
- **THEN** server returns list of guide:// resources and templates

#### Scenario: Resource templates advertised
- **WHEN** client calls `resources/list`
- **THEN** response includes resourceTemplates with guide:// URI patterns

### Requirement: URI Pattern Structure

The guide:// URI scheme SHALL support the following patterns:

- `guide://help` - Usage information and URI pattern documentation
- `guide://collection/{id}` - Collection content by identifier
- `guide://category/{name}` - Category content by name
- `guide://category/{name}/{docId}` - Document or pattern match within category
- `guide://document/{context}/{docId}` - Document from category or collection context

All patterns SHALL return content as text/markdown or multipart/mixed MIME type.

#### Scenario: Help resource access
- **WHEN** client reads `guide://help`
- **THEN** server returns markdown documentation of URI patterns and usage

#### Scenario: Collection access
- **WHEN** client reads `guide://collection/all`
- **THEN** server returns content from collection "all"

#### Scenario: Category access
- **WHEN** client reads `guide://category/examples`
- **THEN** server returns content matching category "examples" default patterns

#### Scenario: Category document access
- **WHEN** client reads `guide://category/examples/intro`
- **THEN** server returns document "intro" and/or pattern matches for "intro" from category "examples"

#### Scenario: Document-only access
- **WHEN** client reads `guide://document/examples/intro.md`
- **THEN** server returns only document "intro.md" from context "examples" (no pattern matching)

### Requirement: Resource List Response

The `resources/list` handler SHALL return both concrete resources and URI templates.

Concrete resources SHALL include:
- `guide://help` with name "Guide URI Help" and mimeType "text/markdown"

Resource templates SHALL include:
- `guide://collection/{id}` for collection access
- `guide://category/{name}` for category access
- `guide://category/{name}/{docId}` for category document/pattern access
- `guide://document/{context}/{docId}` for document-only access

#### Scenario: Static resources listed
- **WHEN** client calls `resources/list`
- **THEN** response includes `guide://help` in resources array

#### Scenario: Templates listed
- **WHEN** client calls `resources/list`
- **THEN** response includes all guide:// patterns in resourceTemplates array

### Requirement: Resource Read Handler

The `resources/read` handler SHALL parse guide:// URIs and return appropriate content.

URI parsing SHALL extract:
- Scheme (must be "guide")
- Resource type (help, collection, category, document)
- Parameters (id, name, docId, context)

Content retrieval SHALL delegate to content tools implementation.

#### Scenario: URI parsing success
- **WHEN** client reads valid guide:// URI
- **THEN** server parses URI components correctly

#### Scenario: Invalid scheme rejected
- **WHEN** client reads URI with non-guide scheme
- **THEN** server returns error "Invalid URI scheme"

#### Scenario: Content delegation
- **WHEN** URI is parsed successfully
- **THEN** server delegates to content retrieval logic

### Requirement: Category Document Semantics

The pattern `guide://category/{name}/{docId}` SHALL search for both documents and pattern matches.

Search order SHALL be:
1. Exact document match for {docId}
2. Pattern match using {docId} as glob pattern
3. Return combined results if both match

#### Scenario: Document and pattern both match
- **WHEN** {docId} matches both a document name and a pattern
- **THEN** server returns both results combined

#### Scenario: Only document matches
- **WHEN** {docId} matches only a document
- **THEN** server returns single document content

#### Scenario: Only pattern matches
- **WHEN** {docId} matches only as a pattern
- **THEN** server returns pattern-matched content

### Requirement: Document-Only Semantics

The pattern `guide://document/{context}/{docId}` SHALL search only for documents, not patterns.

Context resolution SHALL try:
1. Category with name {context}
2. Collection with id {context}
3. Return first match found

#### Scenario: Document found in category
- **WHEN** {context} is a category name and {docId} exists
- **THEN** server returns document from category

#### Scenario: Document found in collection
- **WHEN** {context} is a collection id and {docId} exists
- **THEN** server returns document from collection

#### Scenario: Context not found
- **WHEN** {context} matches neither category nor collection
- **THEN** server returns error "Context not found"

### Requirement: Content Format

Single document matches SHALL return:
- mimeType: "text/markdown"
- text: plain markdown content

Multiple document matches SHALL return:
- mimeType: "multipart/mixed; boundary=\"guide-boundary\""
- text: MIME multipart format with metadata per part

#### Scenario: Single document response
- **WHEN** URI resolves to one document
- **THEN** response has mimeType "text/markdown" and plain content

#### Scenario: Multiple documents response
- **WHEN** URI resolves to multiple documents
- **THEN** response has mimeType "multipart/mixed" and MIME-formatted content

### Requirement: Help Content

The `guide://help` resource SHALL provide:
- Overview of guide:// URI scheme
- List of supported URI patterns with examples
- Usage instructions for each pattern
- Common use cases and examples

Content SHALL be generated dynamically and supplemented by markdown documentation.

#### Scenario: Help content structure
- **WHEN** client reads `guide://help`
- **THEN** response includes URI pattern documentation and examples

#### Scenario: Help includes all patterns
- **WHEN** client reads `guide://help`
- **THEN** response documents all supported URI patterns

### Requirement: Error Handling

Resource read errors SHALL return appropriate MCP error responses.

Error types SHALL include:
- Invalid URI scheme
- Resource not found
- Context not found
- Content retrieval failure

#### Scenario: Invalid URI format
- **WHEN** URI cannot be parsed
- **THEN** server returns error with clear message

#### Scenario: Resource not found
- **WHEN** URI is valid but resource doesn't exist
- **THEN** server returns "not found" error

#### Scenario: Content retrieval error
- **WHEN** content retrieval fails
- **THEN** server returns error from content layer
