## ADDED Requirements

### Requirement: Unified Frontmatter Processing
The system SHALL provide a single function for processing frontmatter that combines parsing, requirements checking, and field rendering.

#### Scenario: Process frontmatter with requirements met
- **WHEN** `process_frontmatter()` is called with content containing frontmatter and requirements context
- **AND** all `requires-*` directives are satisfied
- **THEN** return `ProcessedFrontmatter` with parsed frontmatter and content
- **AND** instruction and description fields are rendered as templates if present

#### Scenario: Process frontmatter with requirements not met
- **WHEN** `process_frontmatter()` is called with content containing `requires-*` directives
- **AND** requirements context does not satisfy the directives
- **THEN** return None (content filtered)

#### Scenario: Render instruction and description fields
- **WHEN** frontmatter contains `instruction` or `description` fields with template variables
- **AND** render context is provided
- **THEN** render these fields as Mustache templates using the context
- **AND** handle rendering errors gracefully with warning logs

### Requirement: Unified File Processing
The system SHALL provide a single function for processing files that handles both template and non-template files.

#### Scenario: Process template file
- **WHEN** `process_file()` is called with a template file (`.mustache` extension)
- **THEN** parse frontmatter using `process_frontmatter()`
- **AND** render template content using `render_template_content()`
- **AND** return `RenderedContent` with rendered content and metadata

#### Scenario: Process non-template file
- **WHEN** `process_file()` is called with a non-template file
- **THEN** parse frontmatter using `process_frontmatter()`
- **AND** return `RenderedContent` with original content (no template rendering)

#### Scenario: File filtered by requirements
- **WHEN** `process_file()` is called and frontmatter requirements are not met
- **THEN** return None (file filtered)

## MODIFIED Requirements

### Requirement: Template Rendering
The system SHALL render templates using unified frontmatter processing.

**Previous behavior:** Template rendering duplicated frontmatter parsing and instruction/description rendering in multiple locations.

**New behavior:** Template rendering uses `process_frontmatter()` for all frontmatter processing, eliminating duplication.

#### Scenario: Render template with frontmatter
- **WHEN** `render_template()` is called with a template file
- **THEN** use `process_frontmatter()` to parse and process frontmatter
- **AND** render template content with processed context
- **AND** return `RenderedContent` with all metadata

### Requirement: Partial Template Loading
The system SHALL load partial templates using unified frontmatter processing.

**Previous behavior:** Partial loading duplicated frontmatter parsing and requirements checking.

**New behavior:** Partial loading uses `process_frontmatter()` for consistency.

#### Scenario: Load partial with requirements
- **WHEN** loading a partial template with `requires-*` directives
- **THEN** use `process_frontmatter()` to check requirements
- **AND** return empty content if requirements not met
- **AND** preserve frontmatter metadata

### Requirement: Command Discovery
The system SHALL discover commands using unified frontmatter processing.

**Previous behavior:** Command discovery parsed frontmatter inline with custom logic.

**New behavior:** Command discovery uses `process_frontmatter()` for consistency.

#### Scenario: Discover commands with requirements
- **WHEN** discovering commands in the commands directory
- **THEN** use `process_frontmatter()` to parse command frontmatter
- **AND** filter commands based on `requires-*` directives
- **AND** extract metadata (description, usage, aliases, category)

### Requirement: Content Retrieval
The system SHALL retrieve content using unified file processing.

**Previous behavior:** Content retrieval duplicated template vs non-template branching logic.

**New behavior:** Content retrieval uses `process_file()` for all files.

#### Scenario: Retrieve template content
- **WHEN** retrieving content from a category containing template files
- **THEN** use `process_file()` to process each file
- **AND** handle template rendering automatically
- **AND** filter files based on requirements

#### Scenario: Retrieve non-template content
- **WHEN** retrieving content from a category containing non-template files
- **THEN** use `process_file()` to process each file
- **AND** parse frontmatter without template rendering
- **AND** filter files based on requirements
