## ADDED Requirements

### Requirement: Template Partial Includes
The template system SHALL support including partial templates via frontmatter includes specification.

#### Scenario: Basic partial inclusion
- **WHEN** a template specifies `includes: [partials/project.mustache]` in frontmatter
- **THEN** the partial content is registered with the Mustache renderer
- **AND** the partial can be referenced as `{{>project}}` in the template

#### Scenario: Multiple partials
- **WHEN** a template specifies multiple includes in frontmatter
- **THEN** all partials are registered and available for use
- **AND** each partial receives the full template context

### Requirement: Partial Path Resolution
The system SHALL resolve partial paths relative to the template file's directory.

#### Scenario: Relative path resolution
- **WHEN** template at `templates/status.mustache` includes `partials/project.mustache`
- **THEN** the system resolves to `templates/partials/project.mustache`

#### Scenario: Missing partial handling
- **WHEN** an included partial file does not exist
- **THEN** the system SHALL raise a clear error indicating the missing file path

### Requirement: Partial Context Inheritance
Partial templates SHALL automatically receive the full template context from the parent template.

#### Scenario: Context inheritance
- **WHEN** a partial template uses `{{project_name}}` variable
- **AND** the parent template context contains `project_name`
- **THEN** the partial renders with the inherited context value

### Requirement: Standard Project Display Partial
The system SHALL provide a standard project information display partial.

#### Scenario: Project partial usage
- **WHEN** a template includes the project partial
- **THEN** it displays project name, categories with descriptions, and collections
- **AND** maintains consistent formatting across all templates
