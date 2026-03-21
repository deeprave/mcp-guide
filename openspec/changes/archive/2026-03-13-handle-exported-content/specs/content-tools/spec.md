## ADDED Requirements

### Requirement: System Template Category
The template system SHALL provide a `_system` category for non-feature-specific system templates.

#### Scenario: System templates are discoverable
- **WHEN** the template system initializes
- **THEN** templates in `_system/` directory are discoverable and renderable

#### Scenario: Startup template moved to system category
- **WHEN** startup instructions are requested
- **THEN** the system uses `_system/startup.mustache`

#### Scenario: Update template moved to system category
- **WHEN** update instructions are requested
- **THEN** the system uses `_system/update.mustache`

### Requirement: Export Instruction Template
The system SHALL provide a single template at `_system/_export.mustache` for all export-related instructions.

#### Scenario: Export template receives context
- **WHEN** export_content or get_content renders export instructions
- **THEN** `_system/_export.mustache` template receives export.path, export.force, export.exists, export.expression, and export.pattern

#### Scenario: Template handles export_content instructions
- **WHEN** export_content renders instructions
- **THEN** template provides file write instructions based on export.force flag

#### Scenario: Template handles get_content references
- **WHEN** get_content detects exported content
- **THEN** template provides reference instructions to existing export

#### Scenario: Knowledge indexing instructions for kiro/q-dev
- **WHEN** knowledge tool is available (detected by agent)
- **THEN** template instructs agent to check knowledge base first

#### Scenario: Direct file access fallback
- **WHEN** knowledge tool is not available
- **THEN** template provides file path for direct access

#### Scenario: Overwrite vs create instructions
- **WHEN** export.force=True
- **THEN** template instructs to overwrite existing file
- **WHEN** export.force=False
- **THEN** template instructs to create only (do not overwrite)

### Requirement: Export Content Tool Template Rendering
The export_content tool SHALL render instructions via template instead of hardcoding instruction strings.

#### Scenario: Instructions rendered from template
- **WHEN** export_content completes successfully
- **THEN** instructions are rendered from `_system/_export.mustache` template
- **AND** template receives export.path, export.force, export.exists, export.expression, and export.pattern

#### Scenario: Backward compatibility maintained
- **WHEN** export_content is called
- **THEN** behavior remains consistent with previous implementation
- **AND** all existing tests pass

## MODIFIED Requirements

### Requirement: get_content Tool
The get_content tool SHALL accept an optional `force` boolean parameter to control export-aware behavior.

The get_content tool SHALL provide unified access to content from collections and categories through a single interface.

#### Scenario: Collection content retrieval
- **WHEN** expression matches a collection name
- **THEN** content from all categories in the collection is returned
- **AND** files are deduplicated across categories

#### Scenario: Category content retrieval
- **WHEN** expression matches a category name
- **THEN** content from that category is returned

#### Scenario: Pattern override
- **WHEN** pattern parameter is provided
- **THEN** only files matching the pattern are included
- **AND** category default patterns are ignored

#### Scenario: Default behavior checks exports
- **WHEN** get_content is called without force parameter (defaults to False)
- **AND** the requested expression has been exported
- **THEN** the tool returns reference instructions instead of full content

#### Scenario: Force returns full content
- **WHEN** get_content is called with force=True
- **AND** the requested expression has been exported
- **THEN** the tool returns the full rendered content as normal

#### Scenario: No export entry behaves normally
- **WHEN** get_content is called for an expression that has not been exported
- **THEN** the tool returns full rendered content regardless of force parameter value
