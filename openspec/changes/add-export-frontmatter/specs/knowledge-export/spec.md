## ADDED Requirements

### Requirement: Exported Content Frontmatter

The `export_content` tool SHALL prepend YAML frontmatter to exported payloads so exported files preserve the resolved content semantics of the collected documents.

The exported frontmatter SHALL include:
- `type`: the resolved exported content type
- `instruction`: the resolved exported instruction

The exported payload beneath that frontmatter SHALL remain the same rendered content that `export_content` would otherwise return for the active content format.

#### Scenario: Single document export preserves explicit metadata
- **WHEN** `export_content` exports a single document with resolved type and instruction metadata
- **THEN** the exported content begins with YAML frontmatter
- **AND** the frontmatter contains the resolved `type`
- **AND** the frontmatter contains the resolved `instruction`
- **AND** the rendered body follows after the frontmatter

#### Scenario: Export type defaults to user information
- **WHEN** all collected documents resolve to `user/information`
- **THEN** the exported frontmatter `type` is `user/information`

#### Scenario: Agent information outranks user information
- **WHEN** at least one collected document resolves to `agent/information`
- **AND** no collected document resolves to `agent/instruction`
- **THEN** the exported frontmatter `type` is `agent/information`

#### Scenario: Agent instruction outranks all other types
- **WHEN** at least one collected document resolves to `agent/instruction`
- **THEN** the exported frontmatter `type` is `agent/instruction`

#### Scenario: Export instruction reuses existing multi-document resolution
- **WHEN** `export_content` exports multiple collected documents
- **THEN** the exported frontmatter `instruction` is resolved using the existing instruction handling strategy
- **AND** duplicate instruction content is removed
- **AND** important instruction handling is preserved

#### Scenario: Export preserves rendered payload format
- **WHEN** `export_content` renders content using the active content-format setting
- **THEN** the rendered payload beneath the export frontmatter preserves that format
- **AND** adding export frontmatter does not change the selected body format
