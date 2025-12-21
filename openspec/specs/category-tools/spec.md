# category-tools Specification

## Purpose
TBD - created by archiving change add-category-tools. Update Purpose after archive.
## Requirements
### Requirement: category_list Tool

The system SHALL provide a `category_list` tool that lists all categories.

Arguments:
- `verbose` (optional, boolean): Include full details (defaults to false)

The tool SHALL:
- Return list of all categories in project configuration
- Include name, dir, description, patterns for each category
- Return Result pattern response

#### Scenario: List all categories
- **WHEN** tool is called
- **THEN** return all categories with their configuration

#### Scenario: Empty category list
- **WHEN** no categories exist
- **THEN** return empty list with success

#### Scenario: Verbose mode
- **WHEN** verbose is true
- **THEN** include all fields (name, dir, description, patterns)

#### Scenario: Non-verbose mode
- **WHEN** verbose is false or omitted
- **THEN** include all fields (name, dir, description, patterns)

### Requirement: category_add Tool

The system SHALL provide a `category_add` tool that creates a new category.

Arguments:
- `name` (required, string): Category name
- `dir` (optional, string): Relative directory path (defaults to name if omitted)
- `description` (optional, string): Category description
- `patterns` (optional, array of strings): Glob patterns (defaults to empty array)

The tool SHALL:
- Validate all inputs
- Check category doesn't already exist
- Create category in project configuration
- Persist configuration to disk
- Return Result pattern response

#### Scenario: Create category with minimal args
- **WHEN** name is provided and valid
- **THEN** create category with name as dir and empty patterns

#### Scenario: Create category with all args
- **WHEN** all arguments are provided and valid
- **THEN** create category with specified configuration

#### Scenario: Category already exists
- **WHEN** category with same name already exists
- **THEN** return Result.failure with error_type "already_exists"

#### Scenario: Invalid name
- **WHEN** name fails validation
- **THEN** return Result.failure with error_type "invalid_name"

#### Scenario: Invalid directory
- **WHEN** dir fails validation
- **THEN** return Result.failure with error_type "invalid_dir"

### Requirement: category_remove Tool

The system SHALL provide a `category_remove` tool that deletes a category.

Arguments:
- `name` (required, string): Category name to remove

The tool SHALL:
- Validate category exists
- Remove category from all collections
- Remove category from project configuration
- Persist configuration to disk
- Return Result pattern response

#### Scenario: Remove existing category
- **WHEN** category exists
- **THEN** remove from configuration and all collections

#### Scenario: Category not found
- **WHEN** category doesn't exist
- **THEN** return Result.failure with error_type "not_found"

#### Scenario: Auto-remove from collections
- **WHEN** category is in collections
- **THEN** remove from all collections automatically

### Requirement: category_change Tool

The system SHALL provide a `category_change` tool that replaces category configuration.

Arguments:
- `name` (required, string): Current category name
- `new_name` (optional, string): New name if renaming
- `dir` (optional, string): New directory path
- `description` (optional, string): New description (empty string to clear)
- `patterns` (optional, array of strings): New patterns (replaces all existing)

The tool SHALL:
- Validate category exists
- Validate new_name if provided and doesn't conflict
- Validate all new values
- Replace category configuration
- Update category name in collections if renamed
- Persist configuration to disk
- Return Result pattern response

#### Scenario: Rename category
- **WHEN** new_name is provided and valid
- **THEN** rename category and update in all collections

#### Scenario: Change directory
- **WHEN** dir is provided and valid
- **THEN** update category directory

#### Scenario: Replace patterns
- **WHEN** patterns is provided
- **THEN** replace all existing patterns with new patterns

#### Scenario: Clear description
- **WHEN** description is empty string
- **THEN** remove description from category

#### Scenario: New name conflicts
- **WHEN** new_name already exists as different category
- **THEN** return Result.failure with error_type "name_conflict"

### Requirement: category_update Tool

The system SHALL provide a `category_update` tool that modifies specific category fields.

Arguments:
- `name` (required, string): Category name
- `add_patterns` (optional, array of strings): Patterns to add
- `remove_patterns` (optional, array of strings): Patterns to remove

The tool SHALL:
- Validate category exists
- Add patterns if add_patterns provided
- Remove patterns if remove_patterns provided
- Persist configuration to disk
- Return Result pattern response

#### Scenario: Add patterns
- **WHEN** add_patterns is provided
- **THEN** append patterns to existing patterns

#### Scenario: Remove patterns
- **WHEN** remove_patterns is provided
- **THEN** remove matching patterns from existing patterns

#### Scenario: Add and remove patterns
- **WHEN** both add_patterns and remove_patterns provided
- **THEN** remove first, then add

#### Scenario: Pattern not found for removal
- **WHEN** remove_patterns contains non-existent pattern
- **THEN** ignore silently (idempotent operation)

### Requirement: Category Name Validation

Category names SHALL be validated using existing validation rules.

Validation SHALL enforce:
- Alphanumeric characters, hyphens, underscores only
- Length between 1 and 30 characters
- No leading or trailing hyphens or underscores

#### Scenario: Valid name
- **WHEN** name is "my-category_123"
- **THEN** validation passes

#### Scenario: Invalid characters
- **WHEN** name contains spaces or special characters
- **THEN** validation fails with clear error message

#### Scenario: Name too long
- **WHEN** name exceeds 30 characters
- **THEN** validation fails with clear error message

### Requirement: Directory Path Validation

Directory paths SHALL be validated for safety and correctness.

Validation SHALL enforce:
- Relative paths only (no absolute paths)
- No path traversal (no ".." components)
- Valid filename characters in each path component
- No leading or trailing double underscores "__" in any component
- Defaults to category name if omitted

#### Scenario: Valid relative path
- **WHEN** dir is "docs/examples"
- **THEN** validation passes

#### Scenario: Absolute path rejected
- **WHEN** dir starts with "/" or drive letter
- **THEN** validation fails with error_type "absolute_path"

#### Scenario: Traversal rejected
- **WHEN** dir contains ".."
- **THEN** validation fails with error_type "traversal_attempt"

#### Scenario: Invalid component name
- **WHEN** path component has leading/trailing "__"
- **THEN** validation fails with error_type "invalid_component"

#### Scenario: Default to name
- **WHEN** dir is omitted
- **THEN** use category name as directory

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

### Requirement: Pattern Validation

Patterns SHALL be validated for safety and correctness.

Validation SHALL enforce:
- Valid filename characters
- No leading or trailing double underscores "__"
- May include path separators
- No path traversal (no "..")
- No absolute paths
- Extension is optional

#### Scenario: Valid pattern without extension
- **WHEN** pattern is "intro"
- **THEN** validation passes

#### Scenario: Valid pattern with extension
- **WHEN** pattern is "*.md"
- **THEN** validation passes

#### Scenario: Valid pattern with path
- **WHEN** pattern is "docs/*.md"
- **THEN** validation passes

#### Scenario: Traversal rejected
- **WHEN** pattern contains ".."
- **THEN** validation fails with error_type "traversal_attempt"

#### Scenario: Invalid component
- **WHEN** pattern has leading/trailing "__"
- **THEN** validation fails with error_type "invalid_pattern"

#### Scenario: Absolute path rejected
- **WHEN** pattern starts with "/"
- **THEN** validation fails with error_type "absolute_path"

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

#### Scenario: Successful persistence
- **WHEN** configuration is valid and writable
- **THEN** write to disk immediately and return success

#### Scenario: Write error
- **WHEN** file cannot be written
- **THEN** return Result.failure with error_type "write_error"

#### Scenario: Concurrent access
- **WHEN** another process is writing configuration
- **THEN** wait for lock or return error

#### Scenario: Invalid configuration
- **WHEN** configuration fails validation before write
- **THEN** return error without writing

#### Scenario: Auto-save on every change
- **WHEN** any category tool modifies configuration
- **THEN** configuration is persisted to disk before returning success

### Requirement: Collection Auto-Update

When category is removed or renamed, collections SHALL be updated automatically.

Auto-update SHALL:
- Remove category from all collections when deleted
- Update category name in all collections when renamed
- Persist collection changes with category changes

#### Scenario: Remove from collections on delete
- **WHEN** category_remove is called
- **THEN** remove category from all collections that reference it

#### Scenario: Update collections on rename
- **WHEN** category_change renames category
- **THEN** update category name in all collections that reference it

#### Scenario: No collections affected
- **WHEN** category is not in any collections
- **THEN** operation succeeds without collection updates

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
- **WHEN** category doesn't exist
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

### Requirement: Dict-based Configuration Compatibility

The system SHALL ensure all category tools work correctly with dict-based project configuration.

Category tools SHALL:
- Access categories using `project.categories.get(name)` instead of iterating with `.name` attribute
- Use category name from dict key instead of non-existent `.name` field
- Handle symlinked docroot directories correctly
- Support pattern matching for basename with any extension (e.g., `general` matches `general.md.mustache`)

#### Scenario: Category lookup with dict-based config
- **WHEN** category tools access project categories
- **THEN** use dict key lookup instead of `.name` attribute access

#### Scenario: Symlinked docroot support
- **WHEN** docroot is a symlink to actual content directory
- **THEN** resolve paths consistently for file discovery and relative path calculation

#### Scenario: Pattern matching for basename with extensions
- **WHEN** pattern is `general` and file is `general.md.mustache`
- **THEN** pattern expands to `["general", "general.*", "general.mustache", "general.*.mustache"]`

#### Scenario: File validation allows legitimate dot-prefixed paths
- **WHEN** files exist in `.config` or other legitimate dot-prefixed directories
- **THEN** include files (only exclude `.` and `..` directory entries)

### Requirement: category_list_files Tool

The system SHALL provide a `category_list_files` tool that lists all files in a category directory.

**Arguments Schema:**
```python
class CategoryListFilesArgs(ToolArguments):
    name: str = Field(description="Name of the category to list files from")
```

**Response Format:**
- Success: `Result.ok(list[dict])` where each dict contains:
  - `path`: str - Relative path from category directory
  - `size`: int - File size in bytes
  - `basename`: str - Filename with .mustache extension removed if applicable
- Failure: `Result.failure(message, error_type)` with appropriate error_type

The tool SHALL:
- Validate category exists in project configuration
- Use existing file discovery mechanism with pattern `**/*`
- Return list of files with path and size information
- Strip `.mustache` extension from basenames in output
- Respect existing scan limits (MAX_DOCUMENTS_PER_GLOB, MAX_GLOB_DEPTH)
- Return Result pattern response

#### Scenario: List files in existing category
- **WHEN** category exists and contains files
- **THEN** return list of files with relative paths and sizes

#### Scenario: Category not found
- **WHEN** category doesn't exist in project
- **THEN** return Result.failure with error_type "not_found"

#### Scenario: Empty category directory
- **WHEN** category directory exists but contains no files
- **THEN** return empty list with success

#### Scenario: Template file basename stripping
- **WHEN** category contains template files (.mustache)
- **THEN** return basename without .mustache extension

#### Scenario: Subdirectory traversal
- **WHEN** category contains files in subdirectories
- **THEN** return relative paths including subdirectory structure

#### Scenario: Scan limits respected
- **WHEN** category contains more than MAX_DOCUMENTS_PER_GLOB files
- **THEN** return up to limit and log warning

#### Scenario: No active session
- **WHEN** tool is called without active session
- **THEN** return Result.failure with error_type "no_session"

#### Scenario: Output format
- **WHEN** files are found
- **THEN** return 2-column format with path and size information

#### Scenario: Invalid category name validation
- **WHEN** category name is empty or contains invalid characters
- **THEN** return Result.failure with error_type "validation_error"

#### Scenario: Large file count handling
- **WHEN** category contains many files approaching scan limits
- **THEN** return files up to limit and include appropriate messaging

