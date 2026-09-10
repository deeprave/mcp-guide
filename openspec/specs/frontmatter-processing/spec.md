# frontmatter-processing Specification

## Purpose
TBD - created by archiving change frontmatter-instruction-handling. Update Purpose after archive.

## Requirements

### Requirement: Content-Size HTTP Headers
The MIME formatter MUST use the `content_size` field from FileInfo for HTTP Content-Length headers instead of calculating content length manually.

#### Scenario: Single file MIME formatting
- **WHEN** formatting a single file with MIME formatter
- **THEN** Content-Length header MUST use `file_info.content_size` value
- **AND** Content-Length MUST NOT be calculated using `len(content.encode("utf-8"))`

#### Scenario: Multiple files MIME formatting
- **WHEN** formatting multiple files with MIME formatter
- **THEN** each file's Content-Length header MUST use respective `file_info.content_size` value
- **AND** Content-Length headers MUST reflect processed content size after frontmatter removal

#### Scenario: Content size accuracy after frontmatter processing
- **WHEN** content has frontmatter that gets stripped during processing
- **THEN** Content-Length header MUST reflect the size of processed content (without frontmatter)
- **AND** Content-Length MUST NOT reflect the original file size

### Requirement: Frontmatter Content Stripping
Frontmatter MUST be stripped from content output while metadata is processed separately.

#### Scenario: Content with frontmatter
- **WHEN** processing content with YAML frontmatter
- **THEN** only the content body should be returned to users/agents
- **AND** frontmatter should be processed separately for metadata extraction

### Requirement: Frontmatter Instruction Extraction
The `Instruction` field from frontmatter MUST be used as the Result instruction with fallback to type-based defaults.

#### Scenario: Explicit instruction in frontmatter
- **WHEN** frontmatter contains an `Instruction` field
- **THEN** that instruction MUST be used as the Result instruction

#### Scenario: Missing instruction with type-based fallback
- **WHEN** no `Instruction` field exists in frontmatter
- **THEN** system MUST fall back to type-based default instructions

#### Scenario: Multiple documents with instruction deduplication
- **WHEN** processing multiple documents with instructions
- **THEN** instructions MUST be deduplicated in the final result

### Requirement: Type-Based Content Behavior
The system MUST handle content types with appropriate behavior and default instructions.

#### Scenario: user/information content type
- **WHEN** content type is `user/information`
- **THEN** content is displayed to user
- **AND** default instruction is "Display this information to the user"

#### Scenario: agent/information content type
- **WHEN** content type is `agent/information`
- **THEN** content is processed but not displayed to user
- **AND** default instruction is "For your information and use. Do not display this content to the user."

#### Scenario: agent/instruction content type
- **WHEN** content type is `agent/instruction`
- **THEN** content is processed but not displayed to user
- **AND** frontmatter `Instruction` field MUST be used

### Requirement: Partial Template Support (Basic)
The system SHALL parse the `partials` field in frontmatter and validate every
partial reference before template rendering. Relative references SHALL be
interpreted from the rendering template's location. Absolute references SHALL
be permitted only when their final canonical target is contained within the
configured document root. Home-anchored and environment-variable expansion
syntax SHALL be invalid. Relative references, including those containing parent
components, SHALL be permitted only when the final canonical target is
contained within the configured document root. A reference names the partial
without its leading underscore; underscore filename derivation and extension
handling are separate from reference resolution. The derived underscore-prefixed
filename SHALL remain excluded from ordinary command and category document
discovery.

#### Scenario: Partials field parsing
- **WHEN** frontmatter contains a `partials` field with relative references
  whose canonical targets are inside the document root
- **THEN** the system SHALL parse and accept those partial references
- **AND** provide them for template composition

#### Scenario: Parent-relative in-root partial parsing
- **WHEN** frontmatter contains a relative partial reference with `..`
  components whose final canonical target is inside the document root
- **THEN** the system SHALL accept the reference
- **AND** preserve existing nested-template composition behaviour

#### Scenario: Unsafe partial reference
- **WHEN** frontmatter contains a home-anchored, environment-variable, or
  canonically-out-of-root partial reference
- **THEN** the system SHALL exclude that reference from the rendering set
- **AND** it SHALL log a non-sensitive warning without failing the parent
  template
- **AND** it SHALL not allow the reference to cause a host file read

### Requirement: Argument Requirements Field
Frontmatter SHALL support `argrequired` top-level field to declare command flags that require values.

#### Scenario: Frontmatter with argrequired
- **WHEN** template frontmatter contains:
  ```yaml
  argrequired:
    - tracking
    - issue
  ```
- **THEN** system SHALL parse `argrequired` as list of strings
- **AND** pass this list to command parser for argument processing

#### Scenario: Frontmatter without argrequired field
- **WHEN** template frontmatter does not contain `argrequired` field
- **THEN** system SHALL treat `argrequired` as empty list
- **AND** all flags use default boolean behavior

#### Scenario: Invalid argrequired format
- **WHEN** `argrequired` is not a list (e.g., string or dict)
- **THEN** system SHALL log warning about invalid format
- **AND** treat `argrequired` as empty list
- **AND** continue processing with default behavior

### Requirement: Cache frontmatter preservation
The frontmatter processor SHALL parse the `cache` field for cache-policy resolution while continuing to strip frontmatter from delivered document content.

#### Scenario: Cache field does not leak into content
- **WHEN** a hosted document includes a valid `cache` frontmatter field
- **THEN** the rendered body excludes the frontmatter
- **AND** cache-policy resolution receives the parsed field
