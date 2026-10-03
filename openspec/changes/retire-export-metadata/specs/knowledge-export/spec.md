# Spec Delta

## MODIFIED Requirements

### Requirement: Exported Content Frontmatter

The `export_content` tool SHALL prepend YAML frontmatter to the payload it
returns so a client can preserve the resolved content semantics if it chooses to
write or index that payload. The export operation SHALL not persist an export
destination, timestamp, source metadata hash, or any other export record in
the Guide project.

The exported frontmatter SHALL include:
- `type`: the resolved exported content type
- `instruction`: the resolved exported instruction

The exported payload beneath that frontmatter SHALL remain the same rendered
content that `export_content` would otherwise return for the active content
format.

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

#### Scenario: Export does not alter Guide project state
- **WHEN** a client requests an export
- **THEN** Guide returns the rendered export payload without modifying the bound project's configuration or write permissions
- **AND** later content retrieval returns Guide-rendered content rather than a reference to that client-side export

## ADDED Requirements

### Requirement: Client-owned export destination

`export_content` SHALL treat its requested destination as client-owned output
information. Guide SHALL return the supplied destination for the client to use,
but SHALL not resolve a default destination, select an agent-specific knowledge
directory, validate a client write path, or claim that it created or controls
the file.

#### Scenario: Client selects an export destination
- **WHEN** a client supplies an export destination
- **THEN** Guide returns that destination with the export payload
- **AND** the client remains responsible for deciding whether and how to write or index the payload

### Requirement: Export tracking interface retirement

Guide SHALL not expose persistent export tracking through tools, commands, or
project configuration. Legacy `exports` entries encountered in existing project
configuration SHALL be ignored and SHALL not be written when that configuration
is subsequently saved.

#### Scenario: Existing configuration contains tracked exports
- **WHEN** Guide loads a project configuration containing legacy `exports` data
- **THEN** it accepts the remaining project configuration
- **AND** it does not use the legacy export data to alter content delivery
- **AND** a later save omits the legacy export data

#### Scenario: Client requests retired export tracking
- **WHEN** a client discovers Guide's tools or commands
- **THEN** `list_exports`, `remove_export`, `guide://_export/list`, and `guide://_export/remove` are absent
