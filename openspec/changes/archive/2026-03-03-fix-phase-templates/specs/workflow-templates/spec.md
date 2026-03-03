## ADDED Requirements

### Requirement: Phase-Conditional Content Blocks
Template content SHALL use Mustache conditionals to show phase-specific content only when the referenced phase exists in the current workflow configuration.

#### Scenario: Check phase content conditional
- **GIVEN** a template with content referencing "check" phase
- **WHEN** workflow phases include "check"
- **THEN** render the check-related content
- **WHEN** workflow phases do NOT include "check"
- **THEN** suppress the check-related content

#### Scenario: Review phase content conditional
- **GIVEN** a template with content referencing "review" phase
- **WHEN** workflow phases include "review"
- **THEN** render the review-related content
- **WHEN** workflow phases do NOT include "review"
- **THEN** suppress the review-related content

#### Scenario: Planning phase content conditional
- **GIVEN** a template with content referencing "planning" phase
- **WHEN** workflow phases include "planning"
- **THEN** render the planning-related content
- **WHEN** workflow phases do NOT include "planning"
- **THEN** suppress the planning-related content

#### Scenario: Mandatory phases always available
- **GIVEN** workflow is enabled
- **WHEN** template references "discussion" or "implementation" phases
- **THEN** always render the content (these phases are mandatory)

### Requirement: OpenSpec-Conditional Content Blocks
Template content SHALL use Mustache conditionals to show openspec-specific content only when openspec feature is enabled.

#### Scenario: OpenSpec content when enabled
- **GIVEN** a template with openspec-specific content wrapped in `{{#openspec}}...{{/openspec}}`
- **WHEN** openspec feature is enabled
- **THEN** render the openspec content

#### Scenario: OpenSpec content when disabled
- **GIVEN** a template with openspec-specific content wrapped in `{{#openspec}}...{{/openspec}}`
- **WHEN** openspec feature is disabled
- **THEN** suppress the openspec content

#### Scenario: OpenSpec references without conditionals
- **GIVEN** a template with openspec references (e.g., "openspec/changes/", "tasks.md")
- **WHEN** content is not wrapped in `{{#openspec}}...{{/openspec}}`
- **THEN** this is a bug that must be fixed

### Requirement: Consistent Consent Language
Templates SHALL use "explicit consent or request" language to ensure agents recognize both user consent and user requests as valid explicit permission.

#### Scenario: Consent language includes request
- **GIVEN** a template mentions explicit consent requirements
- **WHEN** the text says "explicit consent"
- **THEN** it MUST also include "or request" to read "explicit consent or request"

#### Scenario: Entry consent language
- **GIVEN** a phase with entry consent requirement
- **WHEN** template uses `{{#workflow.consent.entry}}`
- **THEN** display "EXPLICIT CONSENT OR REQUEST REQUIRED before entering {phase}"

#### Scenario: Exit consent language
- **GIVEN** a phase with exit consent requirement
- **WHEN** template uses `{{#workflow.consent.exit}}`
- **THEN** display "EXPLICIT CONSENT OR REQUEST REQUIRED before transitioning from {phase}"

### Requirement: Dynamic Phase References
Templates SHALL use workflow context variables instead of hardcoding phase names for transitions.

#### Scenario: Next phase reference
- **GIVEN** a template needs to reference the next phase
- **WHEN** using `{{workflow.next}}` variable
- **THEN** display the correct next phase based on current workflow configuration

#### Scenario: Phase-specific next reference
- **GIVEN** a template needs to reference next phase for a specific phase
- **WHEN** using `{{workflow.phases.implementation.next}}` variable
- **THEN** display the next phase after implementation in current workflow

#### Scenario: Hardcoded phase names
- **GIVEN** a template hardcodes a phase name like "check" or "review"
- **WHEN** the phase is used for conditional logic
- **THEN** wrap in `{{#workflow.phases.{phase}}}...{{/workflow.phases.{phase}}}`
- **WHEN** the phase is used for display/reference
- **THEN** use workflow context variables instead
