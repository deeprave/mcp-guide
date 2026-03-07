## REMOVED Requirements

### Requirement: category_list Tool
**Reason**: Consolidated into `category_collection_list` tool
**Migration**: Use `category_collection_list(type="category", verbose=...)` instead

### Requirement: category_remove Tool
**Reason**: Consolidated into `category_collection_remove` tool
**Migration**: Use `category_collection_remove(type="category", name=...)` instead

## ADDED Requirements

### Requirement: category_collection_list Tool

The system SHALL provide a `category_collection_list` tool that lists categories or collections.

Arguments:
- `type` (required, Literal["category", "collection"]): Type of items to list
- `verbose` (optional, boolean): Include full details (defaults to true)

The tool SHALL:
- When type="category": Return list of all categories in project configuration
- When type="collection": Return list of all collections in project configuration
- Include all relevant fields based on type
- Return Result pattern response

#### Scenario: List all categories
- **WHEN** tool is called with type="category"
- **THEN** return all categories with their configuration

#### Scenario: List all collections
- **WHEN** tool is called with type="collection"
- **THEN** return all collections with their configuration

#### Scenario: Verbose mode
- **WHEN** verbose is true
- **THEN** include all fields for the specified type

#### Scenario: Non-verbose mode
- **WHEN** verbose is false
- **THEN** include all fields for the specified type

### Requirement: category_collection_remove Tool

The system SHALL provide a `category_collection_remove` tool that deletes a category or collection.

Arguments:
- `type` (required, Literal["category", "collection"]): Type of item to remove
- `name` (required, string): Name to remove

The tool SHALL:
- When type="category": Remove category from all collections and project configuration
- When type="collection": Remove collection from project configuration
- Validate item exists before removal
- Persist configuration to disk
- Return Result pattern response

#### Scenario: Remove existing category
- **WHEN** type="category" and category exists
- **THEN** remove from configuration and all collections

#### Scenario: Remove existing collection
- **WHEN** type="collection" and collection exists
- **THEN** remove from configuration

#### Scenario: Item not found
- **WHEN** item doesn't exist
- **THEN** return Result.failure with error_type "not_found"

#### Scenario: Auto-remove category from collections
- **WHEN** type="category" and category is in collections
- **THEN** remove from all collections automatically
