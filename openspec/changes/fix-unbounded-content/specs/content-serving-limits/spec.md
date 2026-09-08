## ADDED Requirements

### Requirement: Static global content limits

The server SHALL read optional global `max-content-limit` and
`max-document-limit` settings once during startup. Omitted values SHALL use
500 MB (500,000,000 bytes) and 100 respectively. Values SHALL be positive;
content values SHALL accept decimal `B`, `KB`, `MB`, and `GB` suffixes.

The values SHALL not be written to configuration by default, exposed as a
client or project setting, or changed until process restart.

#### Scenario: Omitted values use static defaults
- **WHEN** the server starts without either setting
- **THEN** it applies the documented defaults without persisting them

### Requirement: Bounded document delivery

`get_content`, category content, and non-command `guide://` document delivery
SHALL reject a response selecting more documents than the configured maximum or
whose source, rendered body, or final serialised response exceeds the configured
content maximum. Failures SHALL use `max_size_exceeded` and SHALL not return a
partial body.

The server SHALL reserve one aggregate UTF-8 byte budget while retaining selected
rendered documents and while adding formatter framing, delimiters, and content.
It SHALL reject an overflowing addition before constructing the final serialised
response.

#### Scenario: A document response exceeds its limit
- **WHEN** a document body or its final formatted response exceeds `max-content-limit`
- **THEN** delivery fails with `max_size_exceeded` without a partial response

#### Scenario: Multiple individually valid documents exceed the aggregate limit
- **WHEN** selected documents are individually within the source limit but their
  rendered content and formatter framing exceed `max-content-limit` together
- **THEN** delivery fails before constructing the aggregate response
