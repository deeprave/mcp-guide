## ADDED Requirements

### Requirement: Frontmatter Conditional Rendering
The system SHALL support frontmatter-based conditional template rendering based on workflow flags and phase requirements.

#### Scenario: Workflow flag requirement matching
- **WHEN** template has `requires-{flag-name}: true` frontmatter
- **THEN** render template only if flag is truthy (not false)
- **WHEN** template has `requires-{flag-name}: false` frontmatter
- **THEN** render template only if flag is falsy

#### Scenario: Workflow phase requirement matching
- **WHEN** template has `requires-workflow: {phase-name}` frontmatter
- **THEN** render template only if workflow contains specified phase
- **WHEN** template has `requires-workflow: !{phase-name}` frontmatter
- **THEN** render template only if workflow does NOT contain specified phase

#### Scenario: Template suppression
- **WHEN** frontmatter requirements are not met
- **THEN** skip template rendering completely with no output or message
- **AND** discard frontmatter content entirely

#### Scenario: Wildcard category rendering
- **WHEN** using wildcard patterns to get category content
- **THEN** apply frontmatter filtering to suppress non-applicable templates
- **AND** present only templates matching current workflow configuration

### Requirement: Phase-Specific Template Collections
The system SHALL support phase-specific template organization for workflow-aware content.

#### Scenario: Phase-specific templates
- **WHEN** category contains templates like `discussion.md`, `planning.md`, `implementation.md`
- **THEN** render only templates matching current workflow phase

#### Scenario: Workflow-aware content retrieval
- **WHEN** calling `get_content("workflow")` with wildcard patterns
- **THEN** return only templates applicable to current workflow state
- **AND** suppress templates not matching current phase requirements
