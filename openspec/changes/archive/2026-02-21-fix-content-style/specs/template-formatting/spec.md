# Spec: Template Formatting

## MODIFIED Requirements

### Requirement: User-facing templates use formatting variables
User-facing templates (type: user/information) SHALL use template variables for markdown formatting instead of literal markdown syntax.

#### Scenario: Heading formatting
- **WHEN** template contains heading text
- **THEN** it SHALL use `{{h1}}` through `{{h6}}` variables
- **AND** SHALL NOT use literal `#` through `######` markers

#### Scenario: Bold formatting
- **WHEN** template contains bold text
- **THEN** it SHALL use `{{b}}text{{b}}` pattern
- **AND** SHALL NOT use literal `**text**` syntax

#### Scenario: Italic formatting
- **WHEN** template contains italic text
- **THEN** it SHALL use `{{i}}text{{i}}` pattern
- **AND** SHALL NOT use literal `*text*` syntax

#### Scenario: Content-style flag respected
- **WHEN** content-style flag is set to "plain"
- **THEN** formatting variables SHALL render as empty strings
- **WHEN** content-style flag is set to "headings"
- **THEN** heading variables SHALL render as markdown markers
- **AND** bold and italic variables SHALL render as empty strings
- **WHEN** content-style flag is set to "full"
- **THEN** all formatting variables SHALL render as markdown markers
