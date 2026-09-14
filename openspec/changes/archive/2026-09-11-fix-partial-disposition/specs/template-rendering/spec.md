## MODIFIED Requirements

### Requirement: Template Partial Frontmatter Merging
The system SHALL merge frontmatter from the parent template and every file-backed partial that actually renders. It SHALL use centralized instruction resolution and SHALL resolve the rendered content disposition from the parent and contributing partials using established disposition precedence.

#### Scenario: Partial overrides parent instruction
- **WHEN** a partial template includes frontmatter with `instruction: ! <text>`
- **THEN** the partial's instruction SHALL override the parent template's instruction

#### Scenario: Partial provides type metadata
- **WHEN** a partial template includes `type:` frontmatter
- **THEN** the partial's type SHALL be preserved and used for instruction resolution
- **AND** the effective rendered disposition SHALL use that type when it has higher precedence than the parent disposition

#### Scenario: Conditional display behavior
- **WHEN** a template conditionally includes a partial based on data availability
- **THEN** the partial's frontmatter SHALL control whether content is displayed or treated as instructions
- **AND** only a partial that renders SHALL contribute to the effective disposition

### Requirement: Policy Include Pre-rendering

The system SHALL support a `policies:` frontmatter key in templates that declares a list of
policy topics the template depends on. Declared topics SHALL be pre-rendered as mustache partials
before the main template renders.

For each declared topic, the system SHALL:
- Resolve the topic against the `policies` category using the project's active configured patterns
  and sub-path filtering for that topic
- Pre-render each matched document individually as a mustache partial
- Preserve each policy document's frontmatter and resolve its contribution using the same rules as regular partial frontmatter
  (fields combined and deduplicated; not stripped)
- Register the pre-rendered content as a mustache partial under the topic key

Templates SHALL reference pre-rendered policy content using standard mustache partial syntax:
`{{> topic/key}}` (e.g. `{{> git/ops}}`). The effective rendered disposition SHALL include only
policy documents whose registered partial is actually rendered.

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

#### Scenario: Policy partial changes disposition
- **WHEN** a rendered policy document has a higher-precedence `type:` than its parent template
- **AND** its policy partial is referenced by the parent
- **THEN** the final rendered content SHALL carry the policy document's effective disposition

#### Scenario: Unreferenced policy partial
- **WHEN** a policy topic is pre-rendered but its partial is not referenced by the parent template
- **THEN** its frontmatter SHALL NOT affect the final rendered disposition
