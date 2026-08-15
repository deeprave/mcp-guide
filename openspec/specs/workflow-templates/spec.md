# workflow-templates Specification

## Purpose
TBD - created by archiving change project-status. Update Purpose after archive.
## Requirements
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

#### Scenario: Optional workflow command phase declarations use explicit phase lists
- **GIVEN** a command template under `src/mcp_guide/templates/_commands/workflow/`
- **AND** the command transitions to an optional workflow phase
- **WHEN** the template declares `requires-workflow`
- **THEN** it MUST use `requires-workflow: [<phase>]` for that phase

#### Scenario: Dynamic phase command validates membership
- **GIVEN** the `phase` workflow command accepts a phase name at runtime
- **WHEN** workflow is enabled and the command is rendered
- **THEN** it MUST validate the requested phase against all configured workflow phases
- **AND** it MUST include non-ordered phases such as `exploration`

### Requirement: Phase-Specific Template Collections
The system SHALL support phase-specific template organization for workflow-aware content.

#### Scenario: Phase-specific templates
- **WHEN** category contains templates like `discussion.md`, `planning.md`, `implementation.md`
- **THEN** render only templates matching current workflow phase

#### Scenario: Workflow-aware content retrieval
- **WHEN** calling `get_content("workflow")` with wildcard patterns
- **THEN** return only templates applicable to current workflow state
- **AND** suppress templates not matching current phase requirements

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

### Requirement: Conditional workflow command detail
Workflow command templates SHALL conditionally render workflow-specific details without using workflow requirements to suppress their general content.

#### Scenario: Workflow requirement is absent
- **WHEN** a workflow command template is discovered while workflow is disabled
- **THEN** its general command content SHALL remain discoverable and renderable

### Requirement: Workflow State-Format Template Guidance
The workflow state-format template SHALL render agent instructions headed “Workflow State File Format” that describe a strictly YAML workflow-file structure with lowercase keys and use `send_file_content` as the exact MCP tool name for returning the complete updated workflow file.

#### Scenario: Required and optional state fields
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL present `phase` as required
- **AND** it SHALL identify `issue`, `tracking`, `description`, and `queue` as optional as applicable
- **AND** it SHALL describe `description` as an optional description
- **AND** it SHALL state that optional lines may be omitted
- **AND** it SHALL state that keys use lowercase names

#### Scenario: Active change and tracking guidance
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL state that `issue` is required for an active change
- **AND** it SHALL state that `tracking` is required only when transitioning issue tracking
- **AND** it SHALL state that the tracker prefix is optional and the tracker identifier is the required tracking value

#### Scenario: Empty queue and update instruction
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL state that an empty queue is omitted
- **AND** it SHALL instruct the agent to update `{{workflow.file}}`
- **AND** it SHALL instruct the agent to use `send_file_content` as the exact MCP tool name
- **AND** it SHALL not include a generic phase-transition reminder
