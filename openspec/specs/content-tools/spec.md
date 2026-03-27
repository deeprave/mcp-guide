# content-tools Specification

## Purpose
TBD - created by archiving change add-content-tools. Update Purpose after archive.
## Requirements
### Requirement: get_content Tool
The get_content tool SHALL accept an optional `force` boolean parameter to control export-aware behavior.

The get_content tool SHALL provide unified access to content from collections and categories through a single interface.

#### Scenario: Collection content retrieval
- **WHEN** expression matches a collection name
- **THEN** content from all categories in the collection is returned
- **AND** files are deduplicated across categories

#### Scenario: Category content retrieval
- **WHEN** expression matches a category name
- **THEN** content from that category is returned

#### Scenario: Pattern override
- **WHEN** pattern parameter is provided
- **THEN** only files matching the pattern are included
- **AND** category default patterns are ignored

#### Scenario: Default behavior checks exports
- **WHEN** get_content is called without force parameter (defaults to False)
- **AND** the requested expression has been exported
- **THEN** the tool returns reference instructions instead of full content

#### Scenario: Force returns full content
- **WHEN** get_content is called with force=True
- **AND** the requested expression has been exported
- **THEN** the tool returns the full rendered content as normal

#### Scenario: No export entry behaves normally
- **WHEN** get_content is called for an expression that has not been exported
- **THEN** the tool returns full rendered content regardless of force parameter value

### Requirement: get_category_content Tool

The system SHALL provide a `get_category_content` tool that retrieves content from a specific category.

Arguments:
- `category` (required, string): Category name
- `pattern` (optional, string): Glob pattern to filter content

The tool SHALL:
- Resolve category by name
- Use default patterns if pattern argument is omitted
- Return Result pattern response

#### Scenario: Category found with default patterns
- **WHEN** category exists and pattern is omitted
- **THEN** return content matching category's default patterns

#### Scenario: Category found with custom pattern
- **WHEN** category exists and pattern is provided
- **THEN** return content matching custom pattern

#### Scenario: Category not found
- **WHEN** category does not exist
- **THEN** return Result.failure with error_type "not_found" and instruction to present error to user

#### Scenario: No content matches
- **WHEN** category exists but no content matches pattern
- **THEN** return Result.failure with error_type "no_matches" and instruction to present error to user

### Requirement: get_collection_content Tool

The system SHALL provide a `get_collection_content` tool that retrieves content from a specific collection.

Arguments:
- `collection` (required, string): Collection ID
- `pattern` (optional, string): Glob pattern to filter content

The tool SHALL:
- Resolve collection by ID
- Use collection's category patterns if pattern argument is omitted
- Return Result pattern response

#### Scenario: Collection found with default patterns
- **WHEN** collection exists and pattern is omitted
- **THEN** return content from collection's categories using their default patterns

#### Scenario: Collection found with custom pattern
- **WHEN** collection exists and pattern is provided
- **THEN** return content matching custom pattern across collection's categories

#### Scenario: Collection not found
- **WHEN** collection does not exist
- **THEN** return Result.failure with error_type "not_found" and instruction to present error to user

#### Scenario: No content matches
- **WHEN** collection exists but no content matches pattern
- **THEN** return Result.failure with error_type "no_matches" and instruction to present error to user

### Requirement: Pattern Matching

Pattern matching SHALL use glob syntax with the following rules:

- `*` matches any characters within a filename
- `**` matches any characters including directory separators
- `?` matches a single character
- `[abc]` matches any character in the set
- If pattern has no extension, match all files with that root name

**Template Discovery (IMPLEMENTED in GUIDE-33)**:
- Templates named as `{basename}.{ext}.mustache` (e.g., `doc.md.mustache`)
- Pattern `*.md` SHALL match both `*.md` and `*.md.mustache` files ✅
- When both template and non-template exist, prefer non-template ✅
- FileInfo SHALL include `basename` field (filename without `.mustache` extension) ✅
- Pattern expansion: search both `pattern` and `pattern.mustache` ✅
- Deduplication: group by basename, prefer non-template ✅
- Status: Implemented in GUIDE-33 with 15 tests passing, 97% coverage

**Template Rendering**: Moved to separate `template-support` feature.

#### Scenario: Wildcard pattern
- **WHEN** pattern is "*.md"
- **THEN** match all markdown files

#### Scenario: Root name pattern
- **WHEN** pattern is "intro" (no extension)
- **THEN** match intro.md, intro.txt, intro.html, etc.

#### Scenario: Specific file pattern
- **WHEN** pattern is "intro.md"
- **THEN** match only intro.md

#### Scenario: Recursive pattern
- **WHEN** pattern is "**/*.py"
- **THEN** match all Python files in all subdirectories

### Requirement: Result Pattern Response

All tools SHALL return responses using the Result pattern (ADR-003).

Success responses SHALL include:
- `success: true`
- `value`: Content string (markdown or MIME multipart)
- `message` (optional): Informational message

Failure responses SHALL include:
- `success: false`
- `error`: Error message
- `error_type`: Classification (not_found, no_matches, invalid_pattern, etc.)
- `instruction`: Agent guidance on how to handle the error

#### Scenario: Success response format
- **WHEN** content is retrieved successfully
- **THEN** return Result.ok(value=content).to_json_str()

#### Scenario: Failure response format
- **WHEN** error occurs
- **THEN** return Result.failure(error=msg, error_type=type, instruction=guidance).to_json_str()

#### Scenario: Agent instruction for not found
- **WHEN** error_type is "not_found"
- **THEN** instruction is "Present this error to the user and take no further action."

#### Scenario: Agent instruction for no matches
- **WHEN** error_type is "no_matches"
- **THEN** instruction is "Present this error to the user so they can correct the pattern. Do NOT attempt corrective action."

### Requirement: Content Formatting

Single document matches SHALL return plain markdown:
- Content as-is from the file
- No additional headers or metadata
- MIME type: text/markdown (implicit)

Multiple document matches SHALL return MIME multipart format:
- Boundary: "guide-boundary"
- Each part with headers: Content-Type, Content-Location, Content-Length
- MIME type: multipart/mixed (implicit)

#### Scenario: Single document format
- **WHEN** pattern matches exactly one document
- **THEN** return plain markdown content without wrapper

#### Scenario: Multiple documents format
- **WHEN** pattern matches multiple documents
- **THEN** return MIME multipart with metadata per part

#### Scenario: MIME part structure
- **WHEN** returning multiple documents
- **THEN** each part includes Content-Type, Content-Location, and Content-Length headers

### Requirement: MIME Multipart Format

MIME multipart responses SHALL follow RFC 2046 format:

```
Content-Type: multipart/mixed; boundary="guide-boundary"

--guide-boundary
Content-Type: text/markdown
Content-Location: guide://category/examples/intro.md
Content-Length: 1234

[content here]

--guide-boundary
Content-Type: text/markdown
Content-Location: guide://category/examples/tutorial.md
Content-Length: 5678

[content here]

--guide-boundary--
```

#### Scenario: MIME boundary format
- **WHEN** creating multipart response
- **THEN** use "--guide-boundary" as separator and "--guide-boundary--" as terminator

#### Scenario: MIME headers per part
- **WHEN** adding document to multipart response
- **THEN** include Content-Type, Content-Location, and Content-Length headers

#### Scenario: Content-Location URI
- **WHEN** document is from category
- **THEN** Content-Location is "guide://category/{name}/{filename}"

### Requirement: Tool Argument Schema

All tools SHALL define argument schemas following ADR-008 tool conventions.

Schema SHALL include:
- Argument name and type
- Required/optional designation
- Description of purpose
- Examples of valid values

#### Scenario: Required argument validation
- **WHEN** required argument is missing
- **THEN** return error before attempting content retrieval

#### Scenario: Optional argument handling
- **WHEN** optional argument is omitted
- **THEN** use default behavior (category default patterns)

#### Scenario: Argument type validation
- **WHEN** argument has wrong type
- **THEN** return error with clear message about expected type

### Requirement: Session Integration

All tools SHALL use session management for project context.

Tools SHALL:
- Call `get_current_session()` to access project configuration
- Return error if no active session
- Use session's project configuration for category/collection resolution

#### Scenario: Active session
- **WHEN** tool is called with active session
- **THEN** use session's project configuration

#### Scenario: No active session
- **WHEN** tool is called without active session
- **THEN** return Result.failure with error_type "no_session"

#### Scenario: Session project access
- **WHEN** retrieving content
- **THEN** use session.get_project() for configuration

### Requirement: Error Types

The system SHALL define the following error types:

- `not_found`: Category or collection does not exist
- `no_matches`: Pattern matches no content
- `invalid_pattern`: Pattern syntax is invalid
- `no_session`: No active project session
- `io_error`: File system error during content retrieval
- `unknown`: Unexpected error

**Note**: `template_error` moved to separate `template-support` feature.

#### Scenario: Error type classification
- **WHEN** error occurs
- **THEN** classify with appropriate error_type

#### Scenario: Error message clarity
- **WHEN** returning error
- **THEN** include specific details about what went wrong

### Requirement: Future Document Support

Tool argument schemas SHALL be designed to accommodate future document-specific arguments.

Current arguments:
- `category_or_collection` / `category` / `collection`
- `pattern` (optional)

Future expansion (reserved):
- `document` (optional): Specific document identifier

#### Scenario: Design for future expansion
- **WHEN** designing tool argument schemas
- **THEN** accommodate future document-specific arguments

### Requirement: System Template Category
The template system SHALL provide a `_system` category for non-feature-specific system templates.

#### Scenario: System templates are discoverable
- **WHEN** the template system initializes
- **THEN** templates in `_system/` directory are discoverable and renderable

#### Scenario: Startup template moved to system category
- **WHEN** startup instructions are requested
- **THEN** the system uses `_system/startup.mustache`

#### Scenario: Update template moved to system category
- **WHEN** update instructions are requested
- **THEN** the system uses `_system/update.mustache`

### Requirement: Export Instruction Template
The system SHALL provide a single template at `_system/_export.mustache` for all export-related instructions.

#### Scenario: Export template receives context
- **WHEN** export_content or get_content renders export instructions
- **THEN** `_system/_export.mustache` template receives export.path, export.force, export.exists, export.expression, and export.pattern

#### Scenario: Template handles export_content instructions
- **WHEN** export_content renders instructions
- **THEN** template provides file write instructions based on export.force flag

#### Scenario: Template handles get_content references
- **WHEN** get_content detects exported content
- **THEN** template provides reference instructions to existing export

#### Scenario: Knowledge indexing instructions for kiro/q-dev
- **WHEN** knowledge tool is available (detected by agent)
- **THEN** template instructs agent to check knowledge base first

#### Scenario: Direct file access fallback
- **WHEN** knowledge tool is not available
- **THEN** template provides file path for direct access

#### Scenario: Overwrite vs create instructions
- **WHEN** export.force=True
- **THEN** template instructs to overwrite existing file
- **WHEN** export.force=False
- **THEN** template instructs to create only (do not overwrite)

### Requirement: Export Content Tool Template Rendering

The export_content tool SHALL check export tracking before rendering to avoid redundant exports.

The tool SHALL:
- Check export tracking for matching (expression, pattern) tuple
- Gather files and compute metadata hash
- If stored hash matches computed hash, return "already exported" message
- If `force=true`, bypass staleness check
- On successful export, upsert tracking entry with computed metadata hash

The export_content tool SHALL render instructions via template instead of hardcoding instruction strings.

Arguments:
- `expression` (required, string): Content expression
- `path` (required, string): Export destination path
- `pattern` (optional, string): Glob pattern filter
- `force` (optional, boolean): Override staleness check (default: false)

#### Scenario: Instructions rendered from template
- **WHEN** export_content completes successfully
- **THEN** instructions are rendered from `_system/_export.mustache` template
- **AND** template receives export.path, export.force, export.exists, export.expression, and export.pattern

#### Scenario: Backward compatibility maintained
- **WHEN** export_content is called
- **THEN** behavior remains consistent with previous implementation
- **AND** all existing tests pass

#### Scenario: Export with unchanged content
- **WHEN** content previously exported and metadata hash unchanged
- **THEN** return message "Content for '{expression}' already exported to {path}. Use force=True to overwrite or if file is missing."

#### Scenario: Export with force flag
- **WHEN** `force=true` provided
- **THEN** bypass staleness check and export content

#### Scenario: Export with changed content
- **WHEN** metadata hash differs from stored hash
- **THEN** export content and update tracking metadata

#### Scenario: First export
- **WHEN** (expression, pattern) tuple not previously exported
- **THEN** export content and create tracking entry
### Requirement: Export Tracking Storage

The system SHALL store export tracking metadata in project configuration as a dict mapping (expression, pattern) tuple to export metadata.

Each export entry SHALL contain:
- Key: `(expression, pattern)` tuple (pattern is None if not provided)
- Value: `path` (export destination), `metadata_hash` (CRC32 hash of file metadata)

The metadata hash SHALL be computed from sorted file metadata entries in format `category:filename:mtime`, concatenated with `|` separator, using CRC32 algorithm formatted as 8 hex characters.

#### Scenario: Track successful export
- **WHEN** `export_content` completes successfully
- **THEN** upsert export entry with (expression, pattern) as key and computed metadata hash

#### Scenario: Re-export same expression with different pattern
- **WHEN** exporting same expression with different pattern
- **THEN** create separate tracking entry

### Requirement: Staleness Detection via Metadata Hash

The system SHALL detect when exported content is unchanged by comparing metadata hashes.

Detection SHALL:
- Gather files for the expression/pattern
- Compute metadata hash from gathered files
- Compare with stored hash from previous export
- Content is stale if hashes differ

The metadata hash SHALL detect changes from:
- File modifications (mtime changes)
- Files added (new entries in hash input)
- Files deleted (missing entries in hash input)
- Pattern changes (different files match)
- Collection membership changes (different categories)
- Category configuration changes (affects file discovery)

#### Scenario: Content unchanged since export
- **WHEN** computed metadata hash equals stored hash
- **THEN** return "already exported" message with export path

#### Scenario: Content changed since export
- **WHEN** computed metadata hash differs from stored hash
- **THEN** proceed with normal export

#### Scenario: No previous export
- **WHEN** (expression, pattern) tuple not in export tracking
- **THEN** proceed with normal export

#### Scenario: File added with old mtime
- **WHEN** file with old mtime added to category
- **THEN** metadata hash changes (new filename entry) and export proceeds

### Requirement: list_exports Tool
The system SHALL provide a `list_exports` tool that returns a list of all tracked content exports with metadata. The tool accepts an `options` parameter (`list[str]`) that controls template rendering via `parse_options`.

#### Scenario: List all exports
- **WHEN** `list_exports` is called with no filter
- **THEN** all entries from `Project.exports` are returned as a JSON array
- **AND** each entry includes expression, pattern, path, exported_at timestamp, and stale indicator

#### Scenario: Filter by glob pattern
- **WHEN** `list_exports` is called with a glob pattern
- **THEN** only exports matching the glob (against expression, pattern, or path) are returned
- **AND** glob matching is case-insensitive

#### Scenario: Empty exports
- **WHEN** `list_exports` is called and no exports exist
- **THEN** an empty array is returned

#### Scenario: Formatted output via options
- **WHEN** `list_exports` is called with non-empty `options`
- **THEN** output is rendered via `_system/_exports-format.mustache`
- **AND** each option is parsed by `parse_options` into the template context
- **AND** truthy flags (e.g. `"verbose"`) become `True` in context
- **AND** key=value pairs (e.g. `"limit=10"`) become string values in context

#### Scenario: Raw JSON output
- **WHEN** `list_exports` is called with empty `options` (default)
- **THEN** raw JSON array is returned without template rendering

#### Scenario: Staleness detection
- **WHEN** `list_exports` computes staleness for an export
- **THEN** it resolves the expression/pattern to get current file list
- **AND** computes metadata_hash from current file mtimes
- **AND** compares to stored hash
- **AND** sets stale=true if hashes differ, stale=false if they match

#### Scenario: Missing export file
- **WHEN** an export's destination file does not exist or is not readable
- **THEN** exported_at is null
- **AND** stale indicator is "unknown"

### Requirement: parse_options Utility
The system SHALL provide a reusable `parse_options` function in `tool_result.py` that converts a list of display option strings into a template context dict.

#### Scenario: Truthy flag
- **WHEN** options list contains `"verbose"`
- **THEN** result dict contains `{"verbose": True}`

#### Scenario: Key=value pair
- **WHEN** options list contains `"limit=10"`
- **THEN** result dict contains `{"limit": "10"}`

#### Scenario: Mixed options
- **WHEN** options list contains `["verbose", "limit=10"]`
- **THEN** result dict contains `{"verbose": True, "limit": "10"}`

#### Scenario: Empty options
- **WHEN** options list is empty
- **THEN** result dict is empty

### Requirement: remove_export Tool
The system SHALL provide a `remove_export` tool that removes export tracking entries from `Project.exports`.

#### Scenario: Remove by exact match
- **WHEN** `remove_export` is called with expression and pattern
- **THEN** the entry with key `(expression, pattern)` is removed from `Project.exports`
- **AND** Result.ok is returned with confirmation message

#### Scenario: Remove expression-only export
- **WHEN** `remove_export` is called with expression and no pattern
- **THEN** the entry with key `(expression, None)` is removed
- **AND** Result.ok is returned

#### Scenario: Export not found
- **WHEN** `remove_export` is called with expression/pattern that doesn't exist
- **THEN** Result.failure is returned with error_type "not_found"
- **AND** message indicates the exact key that was not found

#### Scenario: File not deleted
- **WHEN** `remove_export` successfully removes tracking entry
- **THEN** the actual exported file is NOT deleted
- **AND** only the tracking entry is removed from `Project.exports`
