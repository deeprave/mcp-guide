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
SHALL reject a response containing more documents than the configured maximum,
whose source or rendered template exceeds the configured content maximum, or
whose final serialised response exceeds that maximum. Failures SHALL use
`max_size_exceeded` and SHALL not return a partial body.

The server SHALL reserve one aggregate UTF-8 byte budget only for retained,
non-empty rendered document content. A document filtered by requirements or
rendering as empty SHALL not consume that budget or count toward the document
maximum. The formatter SHALL reject an overflowing framing, delimiter, or content
addition before constructing the final serialised response.

#### Scenario: A document response exceeds its limit
- **WHEN** a document body or its final formatted response exceeds `max-content-limit`
- **THEN** delivery fails with `max_size_exceeded` without a partial response

#### Scenario: Multiple retained documents exceed the aggregate content budget
- **WHEN** individually valid rendered documents consume more than
  `max-content-limit` together
- **THEN** delivery fails before retaining a document that would overflow the
  aggregate content budget

#### Scenario: Filtered or empty documents do not count
- **WHEN** a selected document is filtered by requirements or renders as empty
- **THEN** it does not consume aggregate content budget or count toward the
  document maximum
