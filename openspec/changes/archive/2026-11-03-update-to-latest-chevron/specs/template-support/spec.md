# Spec Delta

## MODIFIED Requirements

### Requirement: Template Lambda Functions (IMPLEMENTED ✅)
The system SHALL provide advanced template functionality through lambda
functions that support complex data formatting and processing.

Template lambda functions SHALL:
- Follow Chevron's declared extension protocols
- Integrate with ChainMap context system for data access
- Support class-based architecture for clean dependency management
- Handle parsing errors gracefully with clear error messages

#### Lambda Function: format_date
The system SHALL provide date formatting capabilities through `format_date`
lambda function.

Date formatting SHALL:
- Accept strftime format patterns as template text
- Parse variable references from template content
- Format datetime objects using Python strftime
- Support all standard strftime format codes

**Usage Pattern**: `{{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}`

#### Scenario: Date formatting with strftime
- **WHEN** template contains `{{#format_date}}%B %d, %Y{{created_at}}{{/format_date}}`
- **AND** context contains `created_at` with datetime(2023, 12, 25)
- **THEN** render as "December 25, 2023"

#### Lambda Function: truncate
The system SHALL provide text truncation capabilities through `truncate` lambda
function.

Text truncation SHALL:
- Accept maximum length as numeric parameter
- Parse variable references from template content
- Truncate text to specified length with ellipses
- Handle edge cases (empty text, negative lengths)

**Usage Pattern**: `{{#truncate}}50{{description}}{{/truncate}}`

#### Scenario: Text truncation with ellipses
- **WHEN** template contains `{{#truncate}}20{{description}}{{/truncate}}`
- **AND** context contains long description text
- **THEN** truncate to 20 characters and append "..."

#### Lambda Function: highlight_code
The system SHALL provide language-labelled Markdown code fencing through the
`highlight_code` lambda function.

Code fencing SHALL:
- Accept programming language as parameter
- Parse code content from variable references
- Generate markdown code blocks with language specification

**Usage Pattern**: `{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}`

#### Scenario: Code fencing with markdown
- **WHEN** template contains `{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}`
- **AND** context contains Python code in `code_snippet`
- **THEN** render as markdown code block with python language tag
