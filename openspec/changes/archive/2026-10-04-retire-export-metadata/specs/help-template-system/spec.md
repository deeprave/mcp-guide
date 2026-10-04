# Spec Delta

## MODIFIED Requirements

### Requirement: Export Command Organization

The `:export/add` command template SHALL support the same handoff-versus-inline execution split used for document ingestion, for stateless export to a configured client write path.

#### Scenario: Export command structure
- **WHEN** export commands are discovered
- **THEN** the retained template is `_commands/export/add.mustache`
- **AND** `add.mustache` has alias 'export' for backward compatibility
- **AND** commands are accessible as `:export/add` and `:export`
- **AND** tracking list/removal commands are absent

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

## REMOVED Requirements

### Requirement: Export List Command

**Reason**: Export tracking is retired.

**Migration**: Use stateless `export_content` or `guide://_export/add` and manage client files locally.

### Requirement: Export Remove Command

**Reason**: Export tracking is retired.

**Migration**: Use stateless `export_content` or `guide://_export/add` and manage client files locally.

### Requirement: Export List Template

**Reason**: Export tracking is retired.

**Migration**: Use stateless `export_content` or `guide://_export/add` and manage client files locally.
