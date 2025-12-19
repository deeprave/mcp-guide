# Template Extensions Specification

## ADDED Requirements

### Requirement: Multiple Template Extension Support
The system SHALL support multiple template file extensions for Mustache/Handlebars templates.

#### Scenario: Supported Extensions
- WHEN a template file uses `.mustache` extension
- THEN it SHALL be recognized and processed as a template
- WHEN a template file uses `.hbs` extension  
- THEN it SHALL be recognized and processed as a template
- WHEN a template file uses `.handlebars` extension
- THEN it SHALL be recognized and processed as a template
- WHEN a template file uses `.chevron` extension
- THEN it SHALL be recognized and processed as a template

#### Scenario: Template Discovery
- WHEN discovering files in a category directory
- THEN the system SHALL find templates with any supported extension
- AND SHALL apply the same processing logic regardless of extension

#### Scenario: File Name Resolution
- WHEN a template file is processed
- THEN the resulting file name SHALL strip the template extension
- AND SHALL be consistent across all supported extensions
- EXAMPLE: `tracking.md.mustache`, `tracking.md.hbs`, `tracking.md.handlebars`, `tracking.md.chevron` all resolve to `tracking.md`

#### Scenario: Backward Compatibility
- WHEN existing `.mustache` templates are present
- THEN they SHALL continue to work without modification
- AND SHALL have identical behavior to before the change

### Requirement: Extension Priority
The system SHALL handle multiple template files with the same base name consistently.

#### Scenario: Extension Precedence
- WHEN multiple template files exist with the same base name but different extensions
- THEN the system SHALL use a consistent precedence order
- AND SHALL prefer the first match found in alphabetical extension order
- EXAMPLE: If both `file.md.hbs` and `file.md.mustache` exist, behavior SHALL be deterministic

### Requirement: Performance Consistency
The system SHALL maintain equivalent performance when supporting multiple extensions.

#### Scenario: Discovery Performance
- WHEN discovering templates with multiple supported extensions
- THEN performance SHALL not degrade significantly compared to single extension support
- AND SHALL scale linearly with the number of files, not extensions
