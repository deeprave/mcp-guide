## ADDED Requirements

### Requirement: File Deduplication in Collections
The system SHALL deduplicate files based on their full relative path rather than basename when processing collections.

#### Scenario: Files with same basename from different categories
- **WHEN** a collection contains multiple categories with files having the same basename
- **THEN** all files SHALL be included in processing using their full relative path as the unique identifier
- **AND** no files SHALL be silently skipped due to basename conflicts

#### Scenario: Unique file identification
- **WHEN** processing files from multiple categories
- **THEN** the system SHALL use the full relative path (e.g., `guide/general.md`, `review/general.md`) as the deduplication key
- **AND** files with identical basenames but different paths SHALL be treated as distinct files

#### Scenario: Backward compatibility
- **WHEN** processing collections with unique basenames across categories
- **THEN** the system SHALL continue to work as before
- **AND** no existing functionality SHALL be broken by the path-based deduplication
