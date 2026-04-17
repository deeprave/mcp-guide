## MODIFIED Requirements

### Requirement: Frontmatter Conditional Rendering
The system SHALL support frontmatter-based conditional template rendering based
on workflow flags and phase requirements.

#### Scenario: Workflow command phase declarations use explicit phase lists
- **GIVEN** a command template under `src/mcp_guide/templates/_commands/workflow/`
- **AND** the command transitions the workflow to one specific phase
- **WHEN** the template declares `requires-workflow`
- **THEN** it MUST use the explicit phase-list form `requires-workflow: [<phase>]`
- **AND** `<phase>` MUST match the phase that the command instructs the agent to
  enter
- **AND** the generic boolean form `requires-workflow: true` MUST NOT be used for
  those single-phase transition commands

#### Scenario: Missing phase declaration on single-phase transition command is invalid
- **GIVEN** a workflow command template that transitions to one specific phase
- **WHEN** the template omits `requires-workflow`
- **THEN** the template metadata is invalid
- **AND** the command must be corrected to declare the referenced phase

#### Scenario: Reset command declares discussion as its target phase
- **GIVEN** the `reset` workflow command resets workflow state and changes the
  phase to discussion
- **WHEN** its frontmatter is declared
- **THEN** it MUST be treated as a discussion transition for
  `requires-workflow` validation
- **AND** it MUST declare `requires-workflow: [discussion]` unless the command is
  redesigned to stop encoding a single target phase

#### Scenario: Dynamic phase command requires explicit validation design
- **GIVEN** the `phase` workflow command accepts a phase name argument at runtime
- **WHEN** its frontmatter is evaluated
- **THEN** the system MUST NOT rely on `requires-workflow: true` as a substitute
  for phase validation
- **AND** the implementation or specification MUST define how runtime phase
  arguments are validated against configured workflow phases
- **AND** that handling MUST be documented distinctly from the single-phase
  transition command pattern
