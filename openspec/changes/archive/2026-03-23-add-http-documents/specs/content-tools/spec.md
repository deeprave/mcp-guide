# Content Tools Specification

## MODIFIED Requirements

### Requirement: get_category_content Tool
The `get_category_content` tool SHALL include cached URL documents alongside local files when delivering category content.

#### Scenario: Category with cached URL documents
- **WHEN** `get_category_content` is called for a category with URL patterns
- **AND** all URL documents are cached
- **THEN** cached URL content is included alongside local file content

#### Scenario: Category with uncached URL documents
- **WHEN** `get_category_content` is called and a URL document is not yet cached
- **THEN** system instructs agent to fetch the URL and submit via `send_file_content`
- **AND** local content is delivered immediately

### Requirement: get_content Tool
The `get_content` tool SHALL include cached URL documents when resolving categories and collections.

#### Scenario: Collection with URL-enabled categories
- **WHEN** `get_content` resolves a collection containing categories with URL patterns
- **THEN** cached URL documents are included in the aggregated content

### Requirement: export_content Tool
The `export_content` tool SHALL include cached URL documents in exported content.

#### Scenario: Export category with URL documents
- **WHEN** `export_content` is called for a category with cached URL documents
- **THEN** exported content includes both local and cached URL documents
