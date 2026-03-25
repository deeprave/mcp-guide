## MODIFIED Requirements

### Requirement: Document upsert mtime check is atomic

The document store `add_document` operation SHALL perform mtime staleness checks within the same transaction as the write, eliminating the TOCTOU race between a separate read and write.

When `mtime` is provided and `force` is not set, the store SHALL compare against the existing row's mtime before writing.

#### Scenario: Skip write when mtime unchanged
- **WHEN** a document is added with mtime equal to the existing document's mtime
- **AND** force is not set
- **THEN** the write is skipped and a staleness indicator is returned

#### Scenario: Skip write when source is older
- **WHEN** a document is added with mtime older than the existing document's mtime
- **AND** force is not set
- **THEN** the write is skipped and a staleness indicator is returned

#### Scenario: Write proceeds when source is newer
- **WHEN** a document is added with mtime newer than the existing document's mtime
- **THEN** the document is upserted normally

#### Scenario: Force bypasses mtime check
- **WHEN** a document is added with force set
- **THEN** the document is upserted regardless of mtime comparison

#### Scenario: No mtime provided
- **WHEN** a document is added without an mtime value
- **THEN** the document is upserted unconditionally
