# category-tools Spec Delta

## ADDED Requirements

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
