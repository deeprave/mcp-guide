# Phase 1: Core Content Retrieval - Task Breakdowns

## Task 1.1: Implement Glob Pattern Matching

**Description**: Implement glob pattern matching functionality to discover files within category directories based on user-provided or default patterns.

**Requirements**:
- Support standard glob syntax: `*`, `**`, `?`, `[abc]`
- Handle extensionless patterns (e.g., `intro` matches `intro.*`)
- Work with relative paths within category directories
- Return list of matching file paths

**Assumptions**:
- Python's `glob` module provides sufficient functionality
- Category directories exist and are accessible
- Patterns are pre-validated (validation happens at tool level)

**Acceptance Criteria**:
- [ ] `*.md` matches all markdown files in directory
- [ ] `**/*.py` matches Python files recursively
- [ ] `intro` (no extension) matches `intro.md`, `intro.txt`, etc.
- [ ] `docs/*.md` matches markdown files in docs subdirectory
- [ ] Returns empty list when no matches found
- [ ] Handles non-existent directories gracefully
- [ ] Unit tests cover all functionality

---

## Task 1.2: Implement File Discovery in Category Directories

**Description**: Implement file discovery that resolves category directory paths and applies glob patterns to find matching files.

**Requirements**:
- Resolve category directory from project configuration
- Construct absolute paths for glob matching
- Handle both default category patterns and override patterns
- Return file metadata (path, size, modification time)

**Assumptions**:
- Project configuration provides category directory paths
- Category directories are relative to project root
- File system permissions allow reading

**Acceptance Criteria**:
- [ ] Resolves category directory from config
- [ ] Applies default patterns when none provided
- [ ] Applies override pattern when provided
- [ ] Returns file paths relative to category directory
- [ ] Includes file metadata in results
- [ ] Handles missing category directory with clear error
- [ ] Unit tests cover all path resolution scenarios

---

## Task 1.3: Implement File Reading and Content Extraction

**Description**: Implement file reading functionality that extracts content from discovered files with proper encoding handling.

**Requirements**:
- Read file content as UTF-8 text
- Handle binary files gracefully (skip or error)
- Preserve file content exactly (no modifications)
- Return content as string

**Assumptions**:
- Files are text-based (markdown, code, etc.)
- UTF-8 encoding is standard
- Files fit in memory (reasonable size limits)

**Acceptance Criteria**:
- [ ] Reads UTF-8 text files correctly
- [ ] Preserves line endings and whitespace
- [ ] Handles empty files
- [ ] Returns clear error for binary files
- [ ] Returns clear error for encoding issues
- [ ] Handles file read permissions errors
- [ ] Unit tests cover various file types and edge cases

---

## Task 1.4: Add Path Resolution and Validation

**Description**: Implement path resolution and validation to ensure safe file access within category boundaries.

**Requirements**:
- Resolve relative paths to absolute paths
- Prevent path traversal attacks (no `..` escaping category dir)
- Validate files exist within category directory
- Normalize paths for consistent comparison

**Assumptions**:
- Category directories are trusted (from config)
- User-provided patterns may be malicious
- File system is case-sensitive (or handle case-insensitive)

**Acceptance Criteria**:
- [ ] Resolves relative paths correctly
- [ ] Rejects paths with `..` that escape category directory
- [ ] Rejects absolute paths outside category directory
- [ ] Normalizes paths (handles `/./`, `//`, etc.)
- [ ] Validates resolved paths are within category bounds
- [ ] Returns clear error for invalid paths
- [ ] Unit tests cover path traversal attempts

---

## Task 1.5: Handle Missing Files/Directories Errors

**Description**: Implement comprehensive error handling for file system operations with clear, actionable error messages.

**Requirements**:
- Detect missing category directories
- Detect missing files
- Detect permission errors
- Return structured error information
- Provide user-friendly error messages

**Assumptions**:
- Errors should not crash the application
- Error messages should guide users to solutions
- Different error types need different handling

**Acceptance Criteria**:
- [ ] Returns `not_found` error for missing category directory
- [ ] Returns `no_matches` error when pattern matches nothing
- [ ] Returns `io_error` for permission denied
- [ ] Returns `io_error` for other file system errors
- [ ] Error messages include specific details (path, reason)
- [ ] Error messages suggest corrective actions
- [ ] Unit tests cover all error scenarios

---

## Task 1.6: Add Unit Tests for Pattern Matching

**Description**: Create comprehensive unit tests for glob pattern matching functionality.

**Requirements**:
- Test all glob syntax variations
- Test edge cases (empty patterns, special characters)
- Test error conditions
- Meet project test coverage standards

**Assumptions**:
- Test fixtures provide sample directory structures
- Tests run in isolated environment
- Tests are fast (no real file I/O where possible)

**Acceptance Criteria**:
- [ ] Tests for `*`, `**`, `?`, `[abc]` syntax
- [ ] Tests for extensionless pattern matching
- [ ] Tests for recursive patterns
- [ ] Tests for no matches scenario
- [ ] Tests for invalid patterns
- [ ] Tests for empty directory
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 1.7: Add Unit Tests for File Operations

**Description**: Create comprehensive unit tests for file reading and path resolution functionality.

**Requirements**:
- Test file reading with various encodings
- Test path resolution and validation
- Test error handling
- Use test fixtures and mocks appropriately

**Assumptions**:
- Test fixtures provide sample files
- Tests use temporary directories
- Tests clean up after themselves

**Acceptance Criteria**:
- [ ] Tests for UTF-8 file reading
- [ ] Tests for empty files
- [ ] Tests for large files
- [ ] Tests for path traversal prevention
- [ ] Tests for permission errors
- [ ] Tests for missing files
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 2.1: Implement Single File Formatter (Plain Markdown)

**Description**: Implement formatter that returns plain markdown content for single file matches.

**Requirements**:
- Return file content as-is (no wrapping)
- Preserve all formatting and whitespace
- No additional headers or metadata
- Simple string return

**Assumptions**:
- Single file match is common case
- Agents prefer simple format when possible
- Content is already validated as text

**Acceptance Criteria**:
- [ ] Returns file content unchanged
- [ ] Preserves line endings
- [ ] Preserves whitespace
- [ ] No additional formatting added
- [ ] Works with empty files
- [ ] Unit tests verify content preservation

---

## Task 2.2: Implement MIME Multipart Formatter (RFC 2046)

**Description**: Implement RFC 2046 compliant MIME multipart/mixed formatter for multiple file matches.

**Requirements**:
- Generate unique boundary string
- Format according to RFC 2046
- Include proper headers per part
- Terminate with final boundary

**Assumptions**:
- Multiple file matches need structured format
- Agents can parse MIME multipart
- Boundary string won't appear in content

**Acceptance Criteria**:
- [ ] Generates unique boundary (e.g., "guide-boundary-{uuid}")
- [ ] Formats with `Content-Type: multipart/mixed; boundary="..."`
- [ ] Each part separated by `--boundary`
- [ ] Final boundary is `--boundary--`
- [ ] Complies with RFC 2046 specification
- [ ] Unit tests verify format structure

---

## Task 2.3: Add Metadata Extraction (Content-Type, Content-Location, Content-Length)

**Description**: Implement metadata extraction for MIME multipart parts including Content-Type, Content-Location, and Content-Length headers.

**Requirements**:
- Extract Content-Type from file extension
- Generate Content-Location URI (guide://category/name/file.md)
- Calculate Content-Length in bytes
- Format headers correctly

**Assumptions**:
- File extensions map to MIME types
- Content-Location uses guide:// URI scheme
- Content-Length is byte count (UTF-8)

**Acceptance Criteria**:
- [ ] `.md` files get `Content-Type: text/markdown`
- [ ] `.txt` files get `Content-Type: text/plain`
- [ ] Content-Location format: `guide://category/{name}/{path}`
- [ ] Content-Length is accurate byte count
- [ ] Headers formatted as `Header: Value\r\n`
- [ ] Unknown extensions default to `text/plain`
- [ ] Unit tests verify all metadata fields

---

## Task 2.4: Implement Boundary Generation

**Description**: Implement unique boundary string generation for MIME multipart responses.

**Requirements**:
- Generate unique boundary per response
- Ensure boundary doesn't appear in content
- Use safe characters only
- Reasonable length

**Assumptions**:
- UUID-based boundaries are sufficiently unique
- Content won't contain boundary string
- Boundary format: `guide-boundary-{uuid}`

**Acceptance Criteria**:
- [ ] Generates unique boundary each time
- [ ] Format: `guide-boundary-{uuid}`
- [ ] Uses only safe characters (alphanumeric, hyphen)
- [ ] Length ≤70 characters (RFC recommendation)
- [ ] Unit tests verify uniqueness
- [ ] Unit tests verify format

---

## Task 2.5: Add Unit Tests for Single File Format

**Description**: Create comprehensive unit tests for single file formatting.

**Requirements**:
- Test content preservation
- Test various file types
- Test edge cases (empty, large)
- Meet project test coverage standards

**Assumptions**:
- Test fixtures provide sample content
- Tests verify exact content match

**Acceptance Criteria**:
- [ ] Tests for markdown files
- [ ] Tests for text files
- [ ] Tests for empty files
- [ ] Tests for files with special characters
- [ ] Tests verify no modifications to content
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 2.6: Add Unit Tests for Multipart Format

**Description**: Create comprehensive unit tests for MIME multipart formatting.

**Requirements**:
- Test RFC 2046 compliance
- Test boundary generation
- Test metadata headers
- Test multiple files
- Meet project test coverage standards

**Assumptions**:
- Tests can parse generated MIME format
- Tests verify structure and content

**Acceptance Criteria**:
- [ ] Tests for 2+ file formatting
- [ ] Tests verify boundary format
- [ ] Tests verify header format
- [ ] Tests verify content preservation
- [ ] Tests verify final boundary terminator
- [ ] Tests for various file types
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 2.7: Validate RFC 2046 Compliance

**Description**: Validate that MIME multipart implementation complies with RFC 2046 specification.

**Requirements**:
- Review RFC 2046 requirements
- Test against RFC examples
- Verify header format
- Verify boundary format
- Document compliance

**Assumptions**:
- RFC 2046 is the authoritative specification
- Standard MIME parsers can parse output
- Compliance is verifiable through testing

**Acceptance Criteria**:
- [ ] Boundary format matches RFC 2046 section 5.1.1
- [ ] Header format matches RFC 2046 requirements
- [ ] Part separation matches RFC 2046
- [ ] Final boundary matches RFC 2046
- [ ] Standard MIME parser can parse output
- [ ] Compliance documented in code comments
- [ ] Integration test with MIME parser library

---

## Task 3.1: Define Argument Schema (category, pattern)

**Description**: Define Pydantic argument schema for get_category_content tool following ADR-008 conventions.

**Requirements**:
- Inherit from ToolArguments base class
- Define `category` (required, string)
- Define `pattern` (optional, string)
- Add field descriptions
- Add validation

**Assumptions**:
- ToolArguments base class exists (from add-category-tools)
- Pydantic provides validation
- Schema generates markdown documentation

**Acceptance Criteria**:
- [ ] Schema class inherits from ToolArguments
- [ ] `category` field is required string
- [ ] `pattern` field is optional string
- [ ] Field descriptions are clear and helpful
- [ ] Schema validates correctly
- [ ] Schema generates proper markdown docs
- [ ] Unit tests verify schema validation

---

## Task 3.2: Implement Tool Function with Session Integration

**Description**: Implement get_category_content tool function with session management integration.

**Requirements**:
- Use @tools.tool decorator
- Accept CategoryContentArgs
- Get session via get_or_create_session()
- Resolve category from project config
- Call content retrieval logic
- Return Result.to_json_str()

**Assumptions**:
- Session management exists (from existing code)
- Tool decorator handles registration
- Result pattern is established

**Acceptance Criteria**:
- [ ] Function decorated with @tools.tool
- [ ] Accepts args and optional ctx parameters
- [ ] Gets session successfully
- [ ] Resolves category from project
- [ ] Calls content retrieval with correct parameters
- [ ] Returns JSON string via Result pattern
- [ ] Handles async properly
- [ ] Unit tests verify integration

---

## Task 3.3: Add Result Pattern Responses

**Description**: Implement Result pattern responses for all success and error cases.

**Requirements**:
- Use Result.ok() for success
- Use Result.failure() for errors
- Include value in success responses
- Include error, error_type, instruction in failures
- Return JSON string via to_json_str()

**Assumptions**:
- Result class exists (from mcp_core)
- to_json_str() method exists
- JSON format is MCP-compatible

**Acceptance Criteria**:
- [ ] Success returns Result.ok(content).to_json_str()
- [ ] Failures return Result.failure(...).to_json_str()
- [ ] Success includes content in `value` field
- [ ] Failures include error message
- [ ] Failures include error_type
- [ ] Failures include agent instruction
- [ ] JSON format is valid
- [ ] Unit tests verify all response formats

---

## Task 3.4: Define Error Types (not_found, no_matches, no_session)

**Description**: Define and implement error types for get_category_content tool.

**Requirements**:
- Define error type constants
- Map exceptions to error types
- Provide clear error messages
- Include specific details in messages

**Assumptions**:
- Error types are strings
- Error messages guide users to solutions
- Different errors need different handling

**Acceptance Criteria**:
- [ ] `not_found` for missing category
- [ ] `no_matches` for pattern with no results
- [ ] `no_session` for missing project context
- [ ] `io_error` for file system errors
- [ ] Error messages include specific details
- [ ] Error messages are user-friendly
- [ ] Unit tests verify error type mapping

---

## Task 3.5: Add Agent Instructions for Each Error Type

**Description**: Define agent instructions for each error type to guide agent behavior.

**Requirements**:
- Define instruction for each error type
- Instructions prevent futile remediation
- Instructions are clear and actionable
- Instructions follow established patterns

**Assumptions**:
- Agents read and follow instructions
- Instructions should prevent wasted effort
- Consistent instruction format is important

**Acceptance Criteria**:
- [ ] `not_found`: "Present this error to the user and take no further action."
- [ ] `no_matches`: "Present this error to the user so they can correct the pattern. Do NOT attempt corrective action."
- [ ] `no_session`: "Inform user that project context is required."
- [ ] `io_error`: "Present this error to the user. File system issue requires user intervention."
- [ ] Instructions included in Result.failure()
- [ ] Instructions documented in code
- [ ] Unit tests verify instructions present

---

## Task 3.6: Register Tool with MCP Server

**Description**: Register get_category_content tool with MCP server using tool decorator.

**Requirements**:
- Use @tools.tool(ArgsClass) decorator
- Tool appears in MCP tool list
- Tool schema is correct
- Tool is callable via MCP

**Assumptions**:
- Tool registration infrastructure exists
- Decorator handles registration automatically
- MCP server is running

**Acceptance Criteria**:
- [ ] Tool decorated with @tools.tool(CategoryContentArgs)
- [ ] Tool appears in server tool list
- [ ] Tool schema matches argument class
- [ ] Tool description is clear
- [ ] Tool is callable via MCP protocol
- [ ] Integration test verifies registration
- [ ] Integration test verifies tool call

---

## Task 3.7: Add Integration Tests for Tool

**Description**: Create integration tests that verify get_category_content tool works end-to-end.

**Requirements**:
- Test tool via MCP protocol
- Test with real project configuration
- Test success and error cases
- Verify Result pattern responses

**Assumptions**:
- Integration test infrastructure exists
- Test projects can be created
- MCP client can call tools

**Acceptance Criteria**:
- [ ] Test successful content retrieval
- [ ] Test with default patterns
- [ ] Test with override pattern
- [ ] Test category not found error
- [ ] Test no matches error
- [ ] Test no session error
- [ ] All tests pass
- [ ] Tests verify JSON response format

---

## Task 3.8: Test Error Cases and Instructions

**Description**: Create comprehensive tests for all error cases and verify agent instructions.

**Requirements**:
- Test each error type
- Verify error messages
- Verify agent instructions
- Test error response format

**Assumptions**:
- Error cases can be triggered in tests
- Error responses follow Result pattern
- Instructions are included in responses

**Acceptance Criteria**:
- [ ] Test `not_found` error and instruction
- [ ] Test `no_matches` error and instruction
- [ ] Test `no_session` error and instruction
- [ ] Test `io_error` error and instruction
- [ ] Verify error messages are clear
- [ ] Verify instructions are present
- [ ] Verify JSON response format
- [ ] All tests pass
