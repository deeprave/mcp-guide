## ADDED Requirements

### Requirement: Safe MIME Content Locations

When MIME content formatting emits a `Content-Location`, the system SHALL
construct a valid `guide://` URI by UTF-8 percent-encoding every document
relative-path segment after applying existing template-suffix and content-type
extension rules. It SHALL preserve `/` only as the separator between encoded path
segments.

The formatter SHALL apply the same location construction to single-document and
multipart MIME output. Raw CR, LF, NUL, and other control characters SHALL never
appear in a MIME header value derived from a document name.

#### Scenario: Reserved document-name characters are encoded in single MIME output
- **WHEN** a document name contains a space, percent sign, non-ASCII character, or URI-reserved character
- **THEN** its single-document `Content-Location` contains the corresponding UTF-8 percent-encoded path segment
- **AND** the header remains one CRLF-delimited `Content-Location` field

#### Scenario: Legacy control character name cannot inject multipart header
- **WHEN** a legacy or externally modified stored document name contains CR, LF, NUL, or another control character
- **THEN** each multipart `Content-Location` percent-encodes that character
- **AND** no extra MIME header field is created

#### Scenario: Nested location keeps path boundaries
- **WHEN** a document name has multiple nested path segments
- **THEN** each segment is encoded independently
- **AND** the URI retains the intended `/` path separators
