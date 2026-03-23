# Category Tools Specification

## MODIFIED Requirements

### Requirement: Category Model
The system SHALL provide a Category model with name, directory, patterns, and urls.

The `urls` field SHALL be an optional dict mapping pattern names to URL reference objects containing:
- `url` (required): The source URL (HTTP or HTTPS)
- `refresh` (optional): Refresh interval for staleness checking (default: 7 days)

#### Scenario: Category with URL patterns
- **WHEN** a Category is created with `urls={"api-reference.md": {"url": "https://example.com/api", "refresh": "7d"}}`
- **THEN** category stores URL pattern mappings
- **AND** each pattern maps to a URL and refresh interval

#### Scenario: Category without URLs
- **WHEN** a Category is created without `urls`
- **THEN** category behaves as before with local files only

### Requirement: category_add Tool
The `category_add` tool SHALL accept an optional `urls` parameter for URL document references.

When URLs are provided at add time, the system SHALL:
- Instruct the agent to fetch each URL and convert content to markdown
- Accept the converted content back via `send_file_content` with the document cache format
- Cache the content persistently under the assigned pattern
- Only add the URL/pattern to the category after successful caching

#### Scenario: Add category with URL pattern
- **WHEN** `category_add` is called with `urls={"spec.md": {"url": "https://example.com/spec"}}`
- **THEN** system instructs agent to fetch the URL
- **AND** agent converts content to markdown and sends back
- **AND** content is cached under pattern "spec.md"
- **AND** URL/pattern is added to category

#### Scenario: URL fetch fails at add time
- **WHEN** agent fails to fetch the URL during category add
- **THEN** the URL/pattern is NOT added to the category
- **AND** system returns error indicating fetch failure

### Requirement: URL Support in Pattern-Modifying Tools
All tools that modify category patterns SHALL support URL parameters: `category_change`, `category_update`, and collection equivalents.

#### Scenario: Add URL via category_update
- **WHEN** `category_update` is called with `add_urls={"doc.md": {"url": "https://example.com/doc"}}`
- **THEN** system follows the same fetch-cache-add flow as category_add

#### Scenario: Remove URL via category_update
- **WHEN** `category_update` is called with `remove_urls=["doc.md"]`
- **THEN** URL/pattern is removed from category
- **AND** cached content MAY be evicted

### Requirement: URL Staleness in Listings
The `category_list` and `collection_list` tools SHALL flag URL documents that are stale.

#### Scenario: List category with stale URL document
- **WHEN** a cached URL document has exceeded its refresh interval and been marked stale
- **THEN** listing output indicates the document is stale
