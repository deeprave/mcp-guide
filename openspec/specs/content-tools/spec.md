# content-tools Specification

## Purpose
TBD - created by archiving change add-content-tools. Update Purpose after archive.
## Requirements
### Requirement: get_content Tool

The system SHALL provide a `get_content` tool that retrieves content from either a category or collection.

Arguments:
- `category_or_collection` (required, string): Name of category or ID of collection
- `pattern` (optional, string): Glob pattern to filter content

The tool SHALL:
- Try to resolve as category first, then collection
- Use default patterns if pattern argument is omitted
- Return Result pattern response

#### Scenario: Category content retrieval
- **WHEN** category_or_collection matches a category name
- **THEN** return content from that category using specified or default patterns

#### Scenario: Collection content retrieval
- **WHEN** category_or_collection matches a collection ID
- **THEN** return content from that collection

#### Scenario: Pattern override
- **WHEN** pattern argument is provided
- **THEN** use pattern instead of default category patterns

#### Scenario: Not found
- **WHEN** category_or_collection matches neither category nor collection
- **THEN** return Result.failure with error_type "not_found" and instruction to present error to user

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

