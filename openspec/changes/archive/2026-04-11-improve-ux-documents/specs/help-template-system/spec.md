## MODIFIED Requirements

### Requirement: Template Context Integration

The template context SHALL expose template-friendly agent capability flags in addition to the existing agent identity fields.

#### Scenario: Handoff capability is exposed
- **WHEN** command templates are rendered
- **THEN** the context includes `agent.has_handoff`
- **AND** it defaults to `false` unless explicitly enabled for a validated client

#### Scenario: Normalized-name membership flags are exposed
- **WHEN** command templates are rendered
- **THEN** the context includes `agent.is_<normalized-name>` boolean flags derived from the canonical normalized agent name
- **AND** templates can use these flags for light identity-specific wording

### Requirement: Export Command Organization

The `:export/add` command template SHALL support the same handoff-versus-inline execution split used for document ingestion, while preserving the current export semantics.

#### Scenario: Handoff-capable export execution
- **WHEN** `:export/add` or `:export` is rendered for a client with `agent.has_handoff=true`
- **THEN** the template may instruct the agent to perform export separately when it can still complete the workflow end-to-end, including writing the output file

#### Scenario: Inline export fallback
- **WHEN** `:export/add` or `:export` is rendered for a client with `agent.has_handoff=false`
- **THEN** the template instructs the agent to perform export inline
- **AND** it preserves the existing requirement to write the returned content verbatim to disk

#### Scenario: Standardized fallback wording for export
- **WHEN** the handoff-oriented export path cannot actually be used
- **THEN** the agent uses standardized fallback explanation wording before continuing inline
