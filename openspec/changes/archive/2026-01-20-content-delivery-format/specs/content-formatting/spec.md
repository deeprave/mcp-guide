## ADDED Requirements

### Requirement: ContentFormat Enum
The system SHALL provide a ContentFormat enum with NONE, PLAIN, and MIME values for format selection.

#### Scenario: Format enum values
- **WHEN** selecting content format
- **THEN** system SHALL support NONE for merged content stream
- **AND** system SHALL support PLAIN for plain text with separators
- **AND** system SHALL support MIME for MIME-multipart format

### Requirement: BaseFormatter Implementation
The system SHALL provide a BaseFormatter class that merges file content without separators.

#### Scenario: Merge content without separators
- **WHEN** BaseFormatter.format() is called with file list
- **THEN** system SHALL concatenate all file contents
- **AND** system SHALL not add separators between files
- **AND** system SHALL return merged content stream

### Requirement: Content Format Feature Flag
The system SHALL support content-format-mime feature flag with string values.

#### Scenario: Flag value validation
- **WHEN** setting content-format-mime flag
- **THEN** system SHALL accept None, "none", "plain", or "mime"
- **AND** system SHALL reject any other values
- **AND** system SHALL use "none" as default

#### Scenario: Flag resolution hierarchy
- **WHEN** resolving content-format-mime flag
- **THEN** system SHALL check project flag first
- **AND** system SHALL check global flag second
- **AND** system SHALL use NONE format as default

### Requirement: Enum-Based Format Selection
The system SHALL use ContentFormat enum for format selection instead of ContextVar.

#### Scenario: Format selection from flag
- **WHEN** get_format_from_flag() is called
- **THEN** system SHALL resolve content-format-mime flag
- **AND** system SHALL return ContentFormat.PLAIN for "plain"
- **AND** system SHALL return ContentFormat.MIME for "mime"
- **AND** system SHALL return ContentFormat.NONE for None or "none"

#### Scenario: Pass format through call chain
- **WHEN** content tools resolve format
- **THEN** system SHALL pass ContentFormat enum to render_fileinfos()
- **AND** system SHALL not use ContextVar for format tracking

### Requirement: Template Styling Feature Flag
The system SHALL support template-styling feature flag with string values.

#### Scenario: Template styling validation
- **WHEN** setting template-styling flag
- **THEN** system SHALL accept None, "plain", "headings", or "full"
- **AND** system SHALL reject any other values
