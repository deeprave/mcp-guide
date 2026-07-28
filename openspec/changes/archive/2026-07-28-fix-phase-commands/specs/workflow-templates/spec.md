## MODIFIED Requirements

### Requirement: Frontmatter Conditional Rendering
The system SHALL support frontmatter-based conditional template rendering based
on workflow flags and phase requirements.

#### Scenario: Optional workflow command phase declarations use explicit phase lists
- **GIVEN** a command template under `src/mcp_guide/templates/_commands/workflow/`
- **AND** the command transitions the workflow to one optional phase that may be
  absent from the configured workflow
- **WHEN** the template declares `requires-workflow`
- **THEN** it MUST use the explicit phase-list form `requires-workflow: [<phase>]`
- **AND** `<phase>` MUST match the phase that the command instructs the agent to
  enter
- **AND** the generic boolean form `requires-workflow: true` MUST NOT be used for
  those optional single-phase transition commands

#### Scenario: Missing phase declaration on optional single-phase transition command is invalid
- **GIVEN** a workflow command template that transitions to one specific phase
- **AND** that phase may be absent from the configured workflow
- **WHEN** the template omits `requires-workflow`
- **THEN** the template metadata is invalid
- **AND** the command must be corrected to declare the referenced phase

#### Scenario: Mandatory-phase workflow commands may use boolean workflow requirement
- **GIVEN** a workflow command is valid whenever workflow is enabled because its
  target phase is mandatory or because it is a generic workflow helper
- **WHEN** its frontmatter is declared
- **THEN** it MAY use `requires-workflow: true`
- **AND** it does not need to use explicit phase-list syntax solely to reference
  a mandatory phase

#### Scenario: Dynamic phase command requires explicit validation design
- **GIVEN** the `phase` workflow command accepts a phase name argument at runtime
- **WHEN** its frontmatter is evaluated
- **THEN** the command MAY continue using `requires-workflow: true` for command
  availability
- **AND** the implementation MUST separately validate the requested phase against
  configured workflow phases before normal transition instructions are used

#### Scenario: Workflow-scoped membership helpers validate dynamic phase arguments
- **GIVEN** template rendering runs with workflow enabled
- **WHEN** a template uses workflow-scoped membership helpers with a supplied
  phase value
- **THEN** the helpers MUST test membership against configured workflow phases
- **AND** they MUST use all configured valid phases, including non-ordered phases
  such as `exploration`
- **AND** they MUST NOT rely on ordered-phase sequencing such as `next`
