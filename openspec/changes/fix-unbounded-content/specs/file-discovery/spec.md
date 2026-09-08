## ADDED Requirements

### Requirement: Size-Aware Bounded Content Selection

Document discovery SHALL preserve byte-size metadata for both filesystem and
stored documents without loading a document body. Filesystem metadata SHALL use
the source file byte length; stored-document metadata SHALL represent the UTF-8
byte length of the stored body.

When discovery supports a content request, it SHALL stop selection at the
configured request-wide document-count limit across all expanded expressions and
both sources. It SHALL report that the request limit was exceeded rather than
silently returning a truncated document set.

#### Scenario: Stored document size is available before loading content
- **WHEN** discovery selects a stored document for a content request
- **THEN** the selected document includes its UTF-8 byte size before its body is read
- **AND** discovery does not load the body solely to determine that size

#### Scenario: Multiple expressions exceed the combined document limit
- **WHEN** a content request combines categories or collections whose total distinct documents exceed the configured limit
- **THEN** selection fails with the request document-count limit
- **AND** it does not treat each expression as having an independent limit
