## ADDED Requirements

### Requirement: Bounded Stored Document Content

The document store SHALL reject an add or replacement operation whose UTF-8
document body exceeds the configured maximum document size. It SHALL validate the
size before committing the row, preserving any existing document when a replacement
is rejected.

The document store SHALL also reject a content read whose stored byte size exceeds
the configured maximum before materialising its body for a caller.

#### Scenario: Oversized document addition is rejected
- **WHEN** a caller adds or replaces a stored document larger than the configured document-size limit
- **THEN** the operation fails with `max_size_exceeded`
- **AND** no oversized body is committed

#### Scenario: Existing oversized row is not materialised
- **WHEN** a stored document row larger than the configured document-size limit exists from an earlier version or external database change
- **THEN** a content read fails with `max_size_exceeded`
- **AND** the document body is not returned to the caller
