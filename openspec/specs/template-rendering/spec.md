# template-rendering Specification

## Purpose
TBD - created by archiving change fix-partial-frontmatter-handling. Update Purpose after archive.
## Requirements
### Requirement: Centralized Instruction Resolution
The system SHALL provide a centralized function for resolving instructions from frontmatter that supports override semantics and type-based defaults.

#### Scenario: Important instruction override
- **WHEN** frontmatter includes `instruction: ! <text>`
- **THEN** the instruction SHALL be marked as important and override regular instructions

#### Scenario: Type-based default fallback
- **WHEN** no explicit instruction is provided in frontmatter
- **THEN** the system SHALL use type-based default instruction for the content type

#### Scenario: Instruction deduplication
- **WHEN** multiple sources provide the same instruction
- **THEN** the system SHALL deduplicate at sentence level

### Requirement: Template Partial Frontmatter Merging
The system SHALL merge partial template frontmatter with parent template frontmatter using centralized instruction resolution.

#### Scenario: Partial overrides parent instruction
- **WHEN** a partial template includes frontmatter with `instruction: ! <text>`
- **THEN** the partial's instruction SHALL override the parent template's instruction

#### Scenario: Partial provides type metadata
- **WHEN** a partial template includes `type:` frontmatter
- **THEN** the partial's type SHALL be preserved and used for instruction resolution

#### Scenario: Conditional display behavior
- **WHEN** a template conditionally includes a partial based on data availability
- **THEN** the partial's frontmatter SHALL control whether content is displayed or treated as instructions


### Requirement: Policy Include Pre-rendering

The system SHALL support a `policies:` frontmatter key in templates that declares a list of
policy topics the template depends on. Declared topics SHALL be pre-rendered as mustache partials
before the main template renders.

For each declared topic, the system SHALL:
- Resolve the topic against the `policies` category using the project's active configured patterns
  and sub-path filtering for that topic
- Pre-render each matched document individually as a mustache partial
- Merge frontmatter from each policy document using the same rules as regular partial frontmatter
  (fields combined and deduplicated; not stripped)
- Register the pre-rendered content as a mustache partial under the topic key

Templates SHALL reference pre-rendered policy content using standard mustache partial syntax:
`{{> topic/key}}` (e.g. `{{> git/ops}}`).

#### Scenario: Single policy topic resolved
- **WHEN** a template declares `policies: [git/ops]` and a document is active for `git/ops`
- **THEN** that document is pre-rendered and registered as partial `git/ops` before main rendering

#### Scenario: Multiple policy topics resolved
- **WHEN** a template declares `policies: [git/ops, testing]`
- **THEN** each topic is resolved and pre-rendered independently before main rendering

#### Scenario: Composable topic — multiple documents
- **WHEN** the project's patterns match multiple documents under a topic
- **THEN** all matched documents are concatenated as the partial content for that topic

#### Scenario: Partial referenced in template
- **WHEN** a template contains `{{> git/ops}}`
- **THEN** it renders the pre-rendered policy content for the `git/ops` topic

### Requirement: Policy Partial Context Variables

The system SHALL provide per-document context variables when pre-rendering each policy document.

Each policy document SHALL be rendered with:
- `policy_topic` — the declared topic name (e.g. `git/ops`)
- `policy_category` — the category containing the document (always `policies`)
- `policy_path` — the relative path of the matched document within the category

#### Scenario: Context variables available in policy document
- **WHEN** a policy document is pre-rendered
- **THEN** `policy_topic`, `policy_category`, and `policy_path` are available as template variables

#### Scenario: Distinct paths for distinct documents
- **WHEN** multiple documents match a composable topic
- **THEN** each document is pre-rendered with its own `policy_path` value

### Requirement: Missing Policy Placeholder

The system SHALL render a `_missing_policy` system template as the partial content when a
declared policy topic resolves to zero documents.

The `_missing_policy` template SHALL render content that includes the `INSTRUCTION_MISSING_POLICY`
constant, which informs the AI assistant that no policy has been selected for that topic and it
should proceed without enforcing any specific preference.

The placeholder is informational only — it SHALL NOT cause template rendering to fail.

#### Scenario: No documents selected — placeholder rendered
- **WHEN** a template declares a policy topic and no documents match the project's patterns
- **THEN** the `_missing_policy` template is rendered as the partial content for that topic

#### Scenario: Placeholder is informational
- **WHEN** the `_missing_policy` placeholder is rendered
- **THEN** the AI assistant is instructed to proceed without a specific policy preference
      for the topic, not to treat the absence as an error

### Requirement: Unbound-session template rendering
The system SHALL support rendering `_system/` category templates when no project is
bound to the current session.

When rendering with no bound project:
- `project.*` variables SHALL be empty/absent (existing behaviour — must remain stable)
- `flags` SHALL contain global (feature) flags only, with no project flags merged in
- `feature_flags` SHALL contain global flags (unchanged from bound behaviour)
- `agent.*` variables SHALL be populated from the MCP bootstrap agent info if available,
  or absent if not yet received
- `client.*` variables SHALL be populated from TaskManager cached data if available,
  or absent if not yet received
- `server.*`, formatting variables, `tool_prefix`, `@`, and transient timestamp
  variables SHALL always be available

The rendering pipeline SHALL NOT raise an exception when called with an unbound session.
Any missing project variable SHALL silently default to its empty value, consistent with
how `_build_project_context()` already behaves.

#### Scenario: Render _system template with unbound session
- **WHEN** `render_content(pattern, "_system", extra_context)` is called
- **AND** no project is bound to the current session
- **THEN** the template renders without raising an exception
- **AND** `project.*` variables in the rendered output are empty or absent
- **AND** `feature_flags` contains global flags
- **AND** `agent.*` and `client.*` variables are present if bootstrap data is available

#### Scenario: Render _system template with bound session is unchanged
- **WHEN** `render_content(pattern, "_system", extra_context)` is called
- **AND** a project is bound to the current session
- **THEN** the template renders identically to existing behaviour
- **AND** all project, flag, workflow and client_working_dir variables are populated
  as before

#### Scenario: Missing project variable does not raise
- **WHEN** a `_system/` template references `{{project.name}}` with no bound project
- **THEN** the mustache renderer produces an empty string for that variable
- **AND** no exception is raised
