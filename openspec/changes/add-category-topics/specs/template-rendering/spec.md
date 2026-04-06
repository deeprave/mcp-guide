## ADDED Requirements

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
