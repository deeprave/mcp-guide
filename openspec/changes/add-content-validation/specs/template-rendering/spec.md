## ADDED Requirements

### Requirement: Mustache Variable Linting
The template rendering system SHALL provide a variable linter that identifies template variable references not present in any known context for a given document type.

#### Scenario: Undefined variable reference flagged
- **WHEN** a template references `{{unknown.variable}}`
- **THEN** the linter SHALL report a warning with the document path and variable name

#### Scenario: Known context variable accepted
- **WHEN** a template references `{{workflow.phase}}` and the `workflow` feature flag is enabled
- **THEN** the linter SHALL accept the reference without issue

#### Scenario: Section guard variables excluded from strict checking
- **WHEN** a template uses `{{#workflow}}...{{/workflow}}` as a conditional section
- **THEN** the linter SHALL treat `workflow` as a guard and not flag its absence from strict variable checking

#### Scenario: Partial variable references included in lint scope
- **WHEN** a template includes a partial via `{{>partial}}`
- **THEN** variables referenced in the partial SHALL be included in the lint scope for the parent document

### Requirement: Guide URI Validation
The template rendering system SHALL validate `guide://` URI references embedded in templates to ensure they resolve to existing content.

#### Scenario: Valid guide URI accepted
- **WHEN** a template contains `guide://collection/my-collection` and that collection exists
- **THEN** the validator SHALL accept the URI without issue

#### Scenario: Broken guide URI flagged as error
- **WHEN** a template contains a `guide://` URI that does not resolve to any known document, category, collection, or command
- **THEN** the validator SHALL report it as an error with the document path and the unresolvable URI
