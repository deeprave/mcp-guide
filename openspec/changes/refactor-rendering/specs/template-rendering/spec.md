## MODIFIED Requirements

### Requirement: Template Content Rendering
The system SHALL render template content using unified file processing.

**Previous behavior:** Template rendering had separate code paths for template vs non-template files in multiple locations.

**New behavior:** Single `process_file()` function handles both template and non-template files consistently.

#### Scenario: Render template file through unified pipeline
- **WHEN** rendering a template file via any pipeline (commands, content, partials)
- **THEN** use `process_file()` as single entry point
- **AND** automatically detect template vs non-template
- **AND** apply consistent frontmatter processing

#### Scenario: Render non-template file through unified pipeline
- **WHEN** rendering a non-template file via any pipeline
- **THEN** use `process_file()` as single entry point
- **AND** parse frontmatter without template rendering
- **AND** apply consistent requirements checking
