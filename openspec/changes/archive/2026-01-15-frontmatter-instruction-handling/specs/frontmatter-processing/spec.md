# Frontmatter Instruction Handling Specification

## Overview

This specification defines how the content system should process frontmatter to extract instructions and handle different content types appropriately.

## ADDED Requirements

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
The system SHALL support basic parsing of `partials` field in frontmatter for future template composition.

#### Scenario: Partials field parsing
- **WHEN** frontmatter contains a `partials` field
- **THEN** system MUST parse and validate partial references
- **AND** provide foundation for future add-template-partials implementation

## Backward Compatibility

- Existing content without frontmatter continues to work
- Default behavior for unknown types falls back to `user/information`
- Malformed frontmatter doesn't break content processing
- Partial references are parsed but not processed (foundation for future implementation)
