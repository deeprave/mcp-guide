## Purpose

Define finite, configurable budgets for collecting, rendering, and returning
project content so a single request cannot consume unbounded server resources.

## ADDED Requirements

### Requirement: Server-Owned Content Limit Configuration

The system SHALL provide server-owned, positive integer limits with these secure defaults:

- 100 documents selected by one content request
- 1 MiB of UTF-8 source bytes for one document
- 256 KiB of UTF-8 source bytes for one template or partial
- 1 MiB of UTF-8 rendered bytes for one template
- 4 MiB of UTF-8 content returned by one request

The server SHALL allow an operator to configure each limit before startup. A missing
setting SHALL use its default. Zero, negative, non-integer, or unlimited values
SHALL be rejected at startup.

#### Scenario: Defaults bound a content request
- **WHEN** an operator starts the server without content-limit configuration
- **THEN** the server applies all documented default limits
- **AND** no content limit is unbounded

#### Scenario: Invalid content limit prevents startup
- **WHEN** an operator configures a content limit as zero, negative, non-integer, or unlimited
- **THEN** the server refuses to start
- **AND** the startup error identifies the invalid setting

### Requirement: Aggregate Content Request Budget

The system SHALL enforce one aggregate document-count budget and one aggregate
returned-content byte budget for each content request, including `get_content`
and `export_content`. The document-count budget SHALL include every distinct
filesystem or stored document selected through all categories, collections, and
sub-expressions in the request.

The returned-content byte budget SHALL include formatted rendered document content
and export frontmatter when present. The system SHALL reject a request before it
returns content beyond either budget and SHALL NOT return a partial content result.

#### Scenario: Expression exceeds the document-count budget
- **WHEN** a content expression resolves more distinct documents than the configured request limit
- **THEN** the system rejects the request before reading or rendering documents beyond the limit
- **AND** the result identifies the document-count limit

#### Scenario: Formatted content exceeds the request byte budget
- **WHEN** the UTF-8 bytes of a content response, including export frontmatter where applicable, exceed the configured response limit
- **THEN** the system returns a `max_size_exceeded` failure
- **AND** it does not return a partial content payload

### Requirement: Stable Content Limit Failures

The system SHALL report a content-limit failure with error type
`max_size_exceeded`, the limit that was exceeded, and safe remediation
guidance to narrow the request or reduce the source content. It SHALL NOT include
the rejected document body in the failure.

#### Scenario: Oversized content is rejected safely
- **WHEN** a document, template, rendered template, or aggregate response exceeds its applicable content limit
- **THEN** the caller receives `max_size_exceeded`
- **AND** the failure names the applicable limit without disclosing rejected content
