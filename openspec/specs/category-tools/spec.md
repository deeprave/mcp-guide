# category-tools Specification

## Purpose
Define tools for listing, inspecting, and managing configured content categories.
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

### Requirement: category_add Tool creation

The system SHALL provide a `category_add` tool that creates a new category.

The tool SHALL create the category in project configuration. An omitted `dir`
SHALL default to `name`, and omitted `patterns` SHALL default to an empty array.

#### Scenario: Create category with minimal args
- **WHEN** name is provided and valid
- **THEN** create category with name as dir and empty patterns

#### Scenario: Create category with all args
- **WHEN** all arguments are provided and valid
- **THEN** create category with specified configuration

### Requirement: category_add arguments

The `category_add` tool SHALL accept these arguments:

Arguments:
- `name` (required, string): Category name
- `dir` (optional, string): Relative directory path (defaults to name if omitted)
- `description` (optional, string): Category description
- `patterns` (optional, array of strings): Glob patterns (defaults to empty array)

#### Scenario: category_add argument schema
- **WHEN** a client inspects the category_add tool schema
- **THEN** it exposes the documented name, dir, description, and patterns arguments

### Requirement: category_add input validation

The `category_add` tool SHALL validate all inputs and reject a name that is
already configured.

#### Scenario: Category already exists
- **WHEN** category with same name already exists
- **THEN** return Result.failure with error_type "already_exists"

#### Scenario: Invalid name
- **WHEN** name fails validation
- **THEN** return Result.failure with error_type "invalid_name"

#### Scenario: Invalid directory
- **WHEN** dir fails validation
- **THEN** return Result.failure with error_type "invalid_dir"

### Requirement: category_add persistence and response

The `category_add` tool SHALL persist a successfully created category to disk
and return a Result-pattern response.

#### Scenario: Persisted category creation
- **WHEN** category_add creates a valid category
- **THEN** it persists the configuration and returns a successful Result response

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

### Requirement: category_change Tool replacement

The system SHALL provide a `category_change` tool that replaces category configuration.

The tool SHALL replace the specified category configuration. A supplied
`patterns` value SHALL replace all existing patterns, and an empty `description`
SHALL clear the description.

#### Scenario: Change directory
- **WHEN** dir is provided and valid
- **THEN** update category directory

#### Scenario: Replace patterns
- **WHEN** patterns is provided
- **THEN** replace all existing patterns with new patterns

#### Scenario: Clear description
- **WHEN** description is empty string
- **THEN** remove description from category

### Requirement: category_change arguments

The `category_change` tool SHALL accept these arguments:

Arguments:
- `name` (required, string): Current category name
- `new_name` (optional, string): New name if renaming
- `dir` (optional, string): New directory path
- `description` (optional, string): New description (empty string to clear)
- `patterns` (optional, array of strings): New patterns (replaces all existing)

#### Scenario: category_change argument schema
- **WHEN** a client inspects the category_change tool schema
- **THEN** it exposes the documented current-name and replacement-field arguments

### Requirement: category_change validation

The `category_change` tool SHALL validate that the category exists, validate
every new value, and reject a supplied `new_name` that conflicts with another
category.

#### Scenario: New name conflicts
- **WHEN** new_name already exists as different category
- **THEN** return Result.failure with error_type "name_conflict"

### Requirement: category_change collection and persistence effects

When a category is renamed, `category_change` SHALL update its collection
references, persist the configuration to disk, and return a Result-pattern
response.

#### Scenario: Persisted category rename
- **WHEN** category_change renames a valid category
- **THEN** it updates collection references, persists the configuration, and returns a successful Result response

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

### Requirement: Category directory path safety

Directory paths SHALL be relative, SHALL contain no path-traversal component,
and SHALL use valid filename characters in every component. A component SHALL
NOT begin or end with double underscores.

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

### Requirement: Category directory path default

An omitted category directory path SHALL default to the category name.

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

### Requirement: Immediate category configuration persistence

All category tools SHALL persist configuration changes to disk immediately after
modification and SHALL NOT return success until persistence succeeds.

#### Scenario: Successful persistence
- **WHEN** configuration is valid and writable
- **THEN** write to disk immediately and return success

### Requirement: Safe category configuration persistence

Category configuration persistence SHALL use file locking to avoid concurrent
modification, validate configuration before writing, and return a failure when
validation or writing fails.

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

### Requirement: Dictionary-based category configuration

All category tools SHALL work correctly with dictionary-based project
configuration. They SHALL access categories through `project.categories.get(name)`
and use the dictionary key as the category name rather than a `.name` attribute.

#### Scenario: Category lookup with dict-based config
- **WHEN** category tools access project categories
- **THEN** use dict key lookup instead of `.name` attribute access

### Requirement: Category document path compatibility

Category tools SHALL handle symlinked docroot directories consistently and
support a basename pattern with any extension; for example, `general` matches
`general.md.mustache`.

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

The system SHALL provide a `category_list_files` tool that lists a category's
filesystem files and stored documents.

#### Scenario: List all sources (default)
- **WHEN** `category_list_files` is called without a source filter
- **THEN** output includes both filesystem files and stored documents
- **AND** each entry indicates its source

### Requirement: category_list_files source filtering

The tool SHALL accept an optional `source` filter parameter to control which entries are returned:
- `files` — filesystem files only (current behaviour)
- `stored` — stored documents only
- No filter (default) — both filesystem files and stored documents

Each entry in the response SHALL indicate its source (`file` or `store`).

#### Scenario: List filesystem files only
- **WHEN** `category_list_files` is called with source filter `files`
- **THEN** only filesystem files are returned

#### Scenario: List stored documents only
- **WHEN** `category_list_files` is called with source filter `stored`
- **THEN** only stored documents are returned

### Requirement: category_list_files absent-directory handling

A category without a docroot directory SHALL be listed normally with no
filesystem files; its absent directory SHALL NOT be reported as an error.

#### Scenario: No stored documents exist
- **WHEN** `category_list_files` is called for a category with no stored documents
- **THEN** behaviour is unchanged — only filesystem files are listed

#### Scenario: Category without a docroot directory, default source
- **WHEN** `category_list_files` is called without a source filter for a category that exists in configuration and the store but has no directory in the docroot
- **THEN** the stored documents are returned
- **AND** the call succeeds

#### Scenario: Category without a docroot directory, files source
- **WHEN** `category_list_files` is called with source filter `files` for a category that has no directory in the docroot
- **THEN** an empty list is returned
- **AND** the call succeeds

#### Scenario: Category without directory or stored documents
- **WHEN** `category_list_files` is called without a source filter for a category that has no directory and no stored documents
- **THEN** an empty list is returned

### Requirement: Document Remove Tool

The system SHALL provide a `document_remove` MCP tool to delete a document from the store by category and name.

#### Scenario: Remove an existing document
- **WHEN** `document_remove` is called with a valid category and name
- **THEN** the document is removed from the store
- **AND** a success result is returned

#### Scenario: Remove a non-existent document
- **WHEN** `document_remove` is called with a non-existent category/name
- **THEN** an error result is returned

### Requirement: Task-manager document ingestion

The system SHALL provide a `DocumentTask` registered with the task manager that
listens for `FS_FILE_CONTENT` events and ingests documents into the store.

#### Scenario: Ingest a new document
- **WHEN** a `FS_FILE_CONTENT` event contains the required metadata fields
- **AND** no document with that category/name exists
- **THEN** the document is added to the store with auto-detected content-type
- **AND** the event result confirms successful ingestion

### Requirement: Document-ingestion event matching

The DocumentTask SHALL match events from the presence of required metadata
fields rather than path patterns. Other tasks listening for `FS_FILE_CONTENT`
SHALL continue to receive the event independently.

#### Scenario: Unmatched event remains available
- **WHEN** an FS_FILE_CONTENT event does not have the required ingestion metadata
- **THEN** DocumentTask does not match it and other listeners can receive it

### Requirement: Document-ingestion metadata

Document-ingestion event data SHALL contain these required fields:
- `category` — must reference an existing category (validated)
- `name` — document name as stored; defaults to basename of the path if not provided
- `source` — origin identifier (file path or URL)
- `mtime` — source modification time (epoch float)
- `content` — document body

#### Scenario: Event metadata schema
- **WHEN** DocumentTask evaluates an ingestion event
- **THEN** category, name, source, mtime, and content are required metadata fields

### Requirement: Optional document-ingestion metadata

DocumentTask SHALL accept optional `force`, which overwrites regardless
of mtime and defaults to false, and `type`, whose values are
`agent/instruction` by default, `agent/information`, or `user/information`.

#### Scenario: Optional ingestion metadata
- **WHEN** a document-ingestion event supplies force or type metadata
- **THEN** DocumentTask applies the documented optional-field semantics

### Requirement: Document-ingestion content-type detection

DocumentTask SHALL auto-detect Content-Type with the public
`detect_text_subtype` function from `mcp_guide.content.formatters.mime`, store
it in the metadata JSON blob, and SHALL NOT access that function privately.

#### Scenario: Content type is auto-detected
- **WHEN** DocumentTask ingests content
- **THEN** it stores the public-function-detected content type in metadata

#### Scenario: Update with newer mtime
- **WHEN** a `FS_FILE_CONTENT` event matches an existing document
- **AND** the event mtime is newer than the stored mtime
- **THEN** the document content, metadata, and mtime are updated

#### Scenario: Reject update with same mtime
- **WHEN** a `FS_FILE_CONTENT` event matches an existing document
- **AND** the event mtime equals the stored mtime
- **AND** force is not set
- **THEN** the event result returns an error indicating no change

#### Scenario: Force overwrite
- **WHEN** a `FS_FILE_CONTENT` event contains force=true
- **THEN** the document is updated regardless of mtime comparison

#### Scenario: Invalid category
- **WHEN** a `FS_FILE_CONTENT` event references a non-existent category
- **THEN** the event result returns a validation error

#### Scenario: Event without required metadata
- **WHEN** a `FS_FILE_CONTENT` event lacks the required metadata fields
- **THEN** the DocumentTask does not match and the event passes through to other listeners


### Requirement: Category Document Discovery

The system SHALL provide a `discover_category_documents(category, pattern)`
function that returns a category's document paths without rendering content.

#### Scenario: Combined discovery
- **WHEN** the category has both filesystem and stored documents
- **THEN** both sources are included in the returned set without duplication

### Requirement: Category document discovery sources

The function SHALL query the filesystem template corpus and stored project
documents for the category, excluding files and directories with a `_` prefix.

#### Scenario: Filesystem documents discovered
- **WHEN** the category has documents in the filesystem template corpus
- **THEN** those documents are included in the returned set

#### Scenario: Stored documents discovered
- **WHEN** the category has documents stored as project documents
- **THEN** those stored documents are included in the returned set

#### Scenario: Underscore prefix exclusion
- **WHEN** a document or directory has a `_` prefix
- **THEN** it is excluded from the returned set

### Requirement: Category document discovery filtering and order

The function SHALL apply the supplied pattern as a filter, or return all
documents when it is None or empty, and SHALL return results in a consistent,
reproducible order.

#### Scenario: Empty category
- **WHEN** the category has no documents matching the pattern
- **THEN** an empty set is returned

### Requirement: Sub-path Category Filtering

The system SHALL support sub-path filtering in category content resolution when a document
pattern ends with a trailing slash.

Sub-path filtering SHALL use prefix-filter semantics: it narrows the documents matched by the
project's existing configured patterns to those under the specified sub-path prefix. It SHALL
NOT override the project's configured patterns.

#### Scenario: Trailing slash triggers sub-path filtering
- **WHEN** the document pattern ends with `/` (e.g. `"git/ops/"`)
- **THEN** only documents under that sub-path that also match the project's configured patterns
      are returned

#### Scenario: No trailing slash — unchanged behavior
- **WHEN** the document pattern does not end with `/`
- **THEN** existing pattern-matching behavior applies without sub-path filtering

#### Scenario: Configured pattern narrows sub-path results
- **WHEN** a project has configured pattern `git/ops/conservative*` and sub-path filter `git/ops/`
- **THEN** only documents matching `git/ops/conservative*` under `git/ops/` are returned
      (not all documents under `git/ops/`)

#### Scenario: Sub-path with no matching configured patterns
- **WHEN** sub-path filter is applied but no configured patterns match documents under that path
- **THEN** an empty result is returned
