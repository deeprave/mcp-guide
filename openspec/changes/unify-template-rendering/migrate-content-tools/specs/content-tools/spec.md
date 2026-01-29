## MODIFIED Requirements

### Requirement: Content Rendering Integration

The system SHALL use the unified `render_template()` API for all content rendering operations.

The `read_and_render_file_contents()` function SHALL:
- Call `render_template()` for each file requiring rendering
- Handle `RenderedContent` return type from the API
- Extract rendered content and instruction from `RenderedContent` objects
- Preserve existing frontmatter requirement checking behavior
- Maintain file filtering based on `requires-*` directives

#### Scenario: Template file rendering
- **WHEN** a file is identified as a template file
- **THEN** call `render_template()` with file_info, base_dir, project_flags, and template_context
- **AND** extract rendered content from the returned `RenderedContent` object
- **AND** update file_info.content with the rendered content

#### Scenario: Non-template file handling
- **WHEN** a file is not a template file
- **THEN** skip template rendering and use content as-is
- **AND** preserve existing file processing behavior

#### Scenario: Rendering failure
- **WHEN** `render_template()` returns None (filtered or error)
- **THEN** skip the file and add appropriate error message
- **AND** continue processing remaining files

#### Scenario: RenderedContent instruction handling
- **WHEN** `RenderedContent` contains an instruction
- **THEN** preserve the instruction for potential use by calling tools
- **AND** ensure instruction is accessible to content tools

### Requirement: Content Tool Integration

Content tools (`get_content`, `category_content`) SHALL handle `RenderedContent` objects returned from the rendering pipeline.

#### Scenario: Content aggregation with instructions
- **WHEN** multiple files are rendered with instructions
- **THEN** aggregate content appropriately
- **AND** handle instructions according to tool-specific requirements

#### Scenario: Backward compatibility
- **WHEN** processing content through updated rendering pipeline
- **THEN** maintain existing tool behavior and output format
- **AND** ensure no breaking changes to tool interfaces
