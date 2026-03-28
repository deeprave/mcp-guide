## MODIFIED Requirements

### Requirement: get_category_content Tool

The tool SHALL include stored documents matching the category alongside filesystem files when delivering content. Stored documents with a `type` metadata field SHALL be handled according to that type during content rendering.

#### Scenario: Category content includes stored documents
- **WHEN** `get_category_content` is called for a category that has stored documents
- **THEN** stored document content is included alongside filesystem file content

#### Scenario: Category content with no stored documents
- **WHEN** `get_category_content` is called for a category with no stored documents
- **THEN** behaviour is unchanged — only filesystem files are returned

### Requirement: get_content Tool

The tool SHALL include stored documents when resolving categories and collections.

#### Scenario: Collection content includes stored documents
- **WHEN** `get_content` resolves a collection containing categories with stored documents
- **THEN** stored documents are included in the aggregated content

### Requirement: Export Content Tool Template Rendering

The tool SHALL include stored documents in exported content.

#### Scenario: Export includes stored documents
- **WHEN** `export_content` is called for a category with stored documents
- **THEN** exported content includes both filesystem and stored documents
