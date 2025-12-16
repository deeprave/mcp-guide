# category-tools Spec Delta

## ADDED Requirements

### Requirement: category_list_files Tool

The system SHALL provide a `category_list_files` tool that lists all files in a category directory.

Arguments:
- `name` (required, string): Category name

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
