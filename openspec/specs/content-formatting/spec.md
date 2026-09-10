# content-formatting Specification

## Purpose
TBD - created by archiving change content-delivery-format. Update Purpose after archive.

## Requirements

### Requirement: ContentFormat Enum
The system SHALL provide a ContentFormat enum with NONE, PLAIN, and MIME values for format selection.

#### Scenario: Format enum values
- **WHEN** selecting content format
- **THEN** system SHALL support NONE for merged content stream
- **AND** system SHALL support PLAIN for plain text with separators
- **AND** system SHALL support MIME for MIME-multipart format

### Requirement: BaseFormatter Implementation
The system SHALL provide a BaseFormatter class that merges file content without separators.

#### Scenario: Merge content without separators
- **WHEN** BaseFormatter.format() is called with file list
- **THEN** system SHALL concatenate all file contents
- **AND** system SHALL not add separators between files
- **AND** system SHALL return merged content stream

### Requirement: Content Format Feature Flag
The system SHALL support content-format-mime feature flag with string values.

#### Scenario: Flag value validation
- **WHEN** setting content-format-mime flag
- **THEN** system SHALL accept None, "none", "plain", or "mime"
- **AND** system SHALL reject any other values
- **AND** system SHALL use "none" as default

#### Scenario: Flag resolution hierarchy
- **WHEN** resolving content-format-mime flag
- **THEN** system SHALL check project flag first
- **AND** system SHALL check global flag second
- **AND** system SHALL use NONE format as default

### Requirement: Enum-Based Format Selection
The system SHALL use ContentFormat enum for format selection instead of ContextVar.

#### Scenario: Format selection from flag
- **WHEN** get_format_from_flag() is called
- **THEN** system SHALL resolve content-format-mime flag
- **AND** system SHALL return ContentFormat.PLAIN for "plain"
- **AND** system SHALL return ContentFormat.MIME for "mime"
- **AND** system SHALL return ContentFormat.NONE for None or "none"

#### Scenario: Pass format through call chain
- **WHEN** content tools resolve format
- **THEN** system SHALL pass ContentFormat enum to render_fileinfos()
- **AND** system SHALL not use ContextVar for format tracking

### Requirement: Template Styling Feature Flag
The system SHALL support template-styling feature flag with string values.

#### Scenario: Template styling validation
- **WHEN** setting template-styling flag
- **THEN** system SHALL accept None, "plain", "headings", or "full"
- **AND** system SHALL reject any other values

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
