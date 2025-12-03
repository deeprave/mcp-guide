# Specification: Collection Management Tools

**Status**: Selected for Development
**Jira**: GUIDE-101 (Validation), GUIDE-102 (Tools), GUIDE-108 (Integration)
**Implementation**: TDD methodology - tests integrated with implementation

## ADDED Requirements

### Requirement: collection_list Tool

The system SHALL provide a `collection_list` tool that lists all collections.

Arguments:
- `verbose` (optional, boolean): Include full details (defaults to false)

The tool SHALL:
- Return list of all collections in project configuration
- Include name, description, categories for each collection
- Return Result pattern response

### Requirement: collection_add Tool

The system SHALL provide a `collection_add` tool that creates a new collection.

Arguments:
- `name` (required, string): Collection name
- `description` (optional, string): Collection description
- `categories` (optional, array of strings): Category names (defaults to empty array)

The tool SHALL:
- Validate all inputs
- Check collection doesn't already exist
- Validate all referenced categories exist
- Create collection in project configuration
- Persist configuration to disk
- Return Result pattern response

Error types:
- `already_exists` - Collection with same name exists
- `invalid_name` - Name fails validation
- `category_not_found` - Referenced category doesn't exist

### Requirement: collection_remove Tool

The system SHALL provide a `collection_remove` tool that deletes a collection.

Arguments:
- `name` (required, string): Collection name to remove

The tool SHALL:
- Validate collection exists
- Remove collection from project configuration
- Persist configuration to disk
- Return Result pattern response

Error types:
- `not_found` - Collection doesn't exist

### Requirement: collection_change Tool

The system SHALL provide a `collection_change` tool that replaces collection configuration.

Arguments:
- `name` (required, string): Current collection name
- `new_name` (optional, string): New name if renaming
- `description` (optional, string): New description (empty string to clear)
- `categories` (optional, array of strings): New categories (replaces all existing)

The tool SHALL:
- Validate collection exists
- Validate new_name if provided and doesn't conflict
- Validate all new values
- Validate all referenced categories exist
- Replace collection configuration
- Persist configuration to disk
- Return Result pattern response

Error types:
- `not_found` - Collection doesn't exist
- `name_conflict` - New name already exists
- `category_not_found` - Referenced category doesn't exist

### Requirement: collection_update Tool

The system SHALL provide a `collection_update` tool that modifies specific collection fields.

Arguments:
- `name` (required, string): Collection name
- `add_categories` (optional, array of strings): Categories to add
- `remove_categories` (optional, array of strings): Categories to remove

The tool SHALL:
- Validate collection exists
- Add categories if add_categories provided
- Remove categories if remove_categories provided (idempotent - ignore if not present)
- Validate added categories exist
- Persist configuration to disk
- Return Result pattern response

Error types:
- `not_found` - Collection doesn't exist
- `category_not_found` - Added category doesn't exist

### Requirement: Collection Name Validation

Collection names SHALL be validated using existing validation rules.

Validation SHALL enforce:
- Alphanumeric characters, hyphens, underscores only
- Length between 1 and 30 characters
- No leading or trailing hyphens or underscores

### Requirement: Description Validation

Descriptions SHALL be validated for length and content.

Validation SHALL enforce:
- Maximum length of 500 characters
- Valid Unicode characters
- No quote characters (single or double)
- Empty string or omitted is valid (optional field)

Error types:
- `description_too_long` - Exceeds 500 characters
- `invalid_characters` - Contains quotes or invalid characters

### Requirement: Category Reference Validation

Category references SHALL be validated to ensure they exist.

Validation SHALL:
- Check each category name exists in project configuration
- Return error if any category doesn't exist
- Provide list of missing categories in error message

Error types:
- `category_not_found` - One or more categories don't exist (lists all missing)

### Requirement: Configuration Persistence (Auto-Save)

All tools SHALL persist configuration changes to disk IMMEDIATELY after modification.

**CRITICAL**: Configuration MUST be saved automatically on every change. If the user exits without explicit save, changes would be lost. This is an "auto-save" requirement.

Persistence SHALL:
- Save configuration to disk immediately after any modification
- Use file locking to prevent concurrent modification
- Validate configuration before writing
- Handle write errors gracefully
- Return error if persistence fails
- Never return success without persisting changes

Error types:
- `write_error` - File cannot be written
- `lock_error` - Concurrent access conflict

### Requirement: Result Pattern Responses

All tools SHALL return Result pattern responses.

Success responses SHALL include:
- `success: true`
- `value`: Confirmation message or updated configuration
- `message` (optional): Additional information

Failure responses SHALL include:
- `success: false`
- `error`: Error message
- `error_type`: Classification
- `instruction`: Agent guidance

### Requirement: Tool Argument Schemas

All tools SHALL define argument schemas following ADR-008 conventions.

Schemas SHALL include:
- Argument name and type
- Required/optional designation
- Description and examples
- Validation rules

### Requirement: Session Integration

All tools SHALL use session management for project context.

Tools SHALL:
- Call `get_or_create_session()` for project access
- Return error if no active session
- Use session's project configuration

Error types:
- `no_session` - No active session available

### Requirement: Change vs Update Semantics

The system SHALL distinguish between change (replace) and update (modify) operations.

`collection_change` SHALL:
- Replace entire configuration
- Can rename collection
- Replaces all categories (not additive)

`collection_update` SHALL:
- Modify specific fields
- Cannot rename (use change for that)
- Adds/removes categories incrementally
