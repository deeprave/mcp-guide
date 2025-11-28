# Specification: Collection Management Tools

## ADDED Requirements

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

#### Scenario: Create collection with minimal args
- **WHEN** name is provided and valid
- **THEN** create collection with empty categories

#### Scenario: Create collection with categories
- **WHEN** categories are provided and all exist
- **THEN** create collection with specified categories

#### Scenario: Collection already exists
- **WHEN** collection with same name already exists
- **THEN** return Result.failure with error_type "already_exists"

#### Scenario: Invalid name
- **WHEN** name fails validation
- **THEN** return Result.failure with error_type "invalid_name"

#### Scenario: Category doesn't exist
- **WHEN** referenced category doesn't exist
- **THEN** return Result.failure with error_type "category_not_found"

### Requirement: collection_remove Tool

The system SHALL provide a `collection_remove` tool that deletes a collection.

Arguments:
- `name` (required, string): Collection name to remove

The tool SHALL:
- Validate collection exists
- Remove collection from project configuration
- Persist configuration to disk
- Return Result pattern response

#### Scenario: Remove existing collection
- **WHEN** collection exists
- **THEN** remove from configuration

#### Scenario: Collection not found
- **WHEN** collection doesn't exist
- **THEN** return Result.failure with error_type "not_found"

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

#### Scenario: Rename collection
- **WHEN** new_name is provided and valid
- **THEN** rename collection

#### Scenario: Replace categories
- **WHEN** categories is provided
- **THEN** replace all existing categories with new categories

#### Scenario: Clear description
- **WHEN** description is empty string
- **THEN** remove description from collection

#### Scenario: New name conflicts
- **WHEN** new_name already exists as different collection
- **THEN** return Result.failure with error_type "name_conflict"

#### Scenario: Category doesn't exist
- **WHEN** referenced category doesn't exist
- **THEN** return Result.failure with error_type "category_not_found"

### Requirement: collection_update Tool

The system SHALL provide a `collection_update` tool that modifies specific collection fields.

Arguments:
- `name` (required, string): Collection name
- `add_categories` (optional, array of strings): Categories to add
- `remove_categories` (optional, array of strings): Categories to remove

The tool SHALL:
- Validate collection exists
- Add categories if add_categories provided
- Remove categories if remove_categories provided
- Validate added categories exist
- Persist configuration to disk
- Return Result pattern response

#### Scenario: Add categories
- **WHEN** add_categories is provided
- **THEN** append categories to existing categories

#### Scenario: Remove categories
- **WHEN** remove_categories is provided
- **THEN** remove matching categories from existing categories

#### Scenario: Add and remove categories
- **WHEN** both add_categories and remove_categories provided
- **THEN** remove first, then add

#### Scenario: Category not found for removal
- **WHEN** remove_categories contains non-existent category
- **THEN** ignore silently (idempotent operation)

#### Scenario: Added category doesn't exist
- **WHEN** add_categories contains non-existent category
- **THEN** return Result.failure with error_type "category_not_found"

### Requirement: Collection Name Validation

Collection names SHALL be validated using existing validation rules.

Validation SHALL enforce:
- Alphanumeric characters, hyphens, underscores only
- Length between 1 and 30 characters
- No leading or trailing hyphens or underscores

#### Scenario: Valid name
- **WHEN** name is "my-collection_123"
- **THEN** validation passes

#### Scenario: Invalid characters
- **WHEN** name contains spaces or special characters
- **THEN** validation fails with clear error message

#### Scenario: Name too long
- **WHEN** name exceeds 30 characters
- **THEN** validation fails with clear error message

### Requirement: Description Validation

Descriptions SHALL be validated for length and content.

Validation SHALL enforce:
- Maximum length of 500 characters
- Valid Unicode characters
- No quote characters (single or double)

#### Scenario: Valid description
- **WHEN** description is under 500 chars with valid Unicode
- **THEN** validation passes

#### Scenario: Description too long
- **WHEN** description exceeds 500 characters
- **THEN** validation fails with error_type "description_too_long"

#### Scenario: Contains quotes
- **WHEN** description contains " or ' characters
- **THEN** validation fails with error_type "invalid_characters"

#### Scenario: Empty description allowed
- **WHEN** description is empty string or omitted
- **THEN** validation passes (optional field)

### Requirement: Category Reference Validation

Category references SHALL be validated to ensure they exist.

Validation SHALL:
- Check each category name exists in project configuration
- Return error if any category doesn't exist
- Provide list of missing categories in error message

#### Scenario: All categories exist
- **WHEN** all referenced categories exist
- **THEN** validation passes

#### Scenario: Category doesn't exist
- **WHEN** referenced category doesn't exist
- **THEN** validation fails with error_type "category_not_found"

#### Scenario: Multiple missing categories
- **WHEN** multiple referenced categories don't exist
- **THEN** error message lists all missing categories

### Requirement: Configuration Persistence

All tools SHALL persist configuration changes to disk safely.

Persistence SHALL:
- Use file locking to prevent concurrent modification
- Validate configuration before writing
- Handle write errors gracefully
- Return error if persistence fails

#### Scenario: Successful persistence
- **WHEN** configuration is valid and writable
- **THEN** write to disk and return success

#### Scenario: Write error
- **WHEN** file cannot be written
- **THEN** return Result.failure with error_type "write_error"

#### Scenario: Concurrent access
- **WHEN** another process is writing configuration
- **THEN** wait for lock or return error

#### Scenario: Invalid configuration
- **WHEN** configuration fails validation before write
- **THEN** return error without writing

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

#### Scenario: Success response
- **WHEN** operation succeeds
- **THEN** return Result.ok with confirmation

#### Scenario: Validation failure
- **WHEN** validation fails
- **THEN** return Result.failure with specific error_type and instruction

#### Scenario: Not found error
- **WHEN** collection doesn't exist
- **THEN** return Result.failure with error_type "not_found"

### Requirement: Tool Argument Schemas

All tools SHALL define argument schemas following ADR-008 conventions.

Schemas SHALL include:
- Argument name and type
- Required/optional designation
- Description and examples
- Validation rules

#### Scenario: Required argument validation
- **WHEN** required argument is missing
- **THEN** return error before processing

#### Scenario: Type validation
- **WHEN** argument has wrong type
- **THEN** return error with expected type

#### Scenario: Optional argument handling
- **WHEN** optional argument is omitted
- **THEN** use default value or skip

### Requirement: Session Integration

All tools SHALL use session management for project context.

Tools SHALL:
- Call `get_current_session()` for project access
- Return error if no active session
- Use session's project configuration

#### Scenario: Active session
- **WHEN** tool is called with active session
- **THEN** use session's project configuration

#### Scenario: No active session
- **WHEN** tool is called without active session
- **THEN** return Result.failure with error_type "no_session"

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

#### Scenario: Change replaces categories
- **WHEN** collection_change is called with categories
- **THEN** replace all existing categories with new list

#### Scenario: Update adds categories
- **WHEN** collection_update is called with add_categories
- **THEN** append to existing categories

#### Scenario: Update removes categories
- **WHEN** collection_update is called with remove_categories
- **THEN** remove from existing categories
