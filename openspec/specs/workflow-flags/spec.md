# workflow-flags Specification

## Purpose
TBD - created by archiving change project-status. Update Purpose after archive.
## Requirements
### Requirement: Workflow File Configuration ✅ IMPLEMENTED
The system SHALL support a configurable workflow state file via the `workflow-file` project flag with variable substitution.

#### Scenario: Default workflow file ✅
- **WHEN** `workflow-file` flag is not set
- **THEN** use `.guide.yaml` as the default workflow state file

#### Scenario: Custom workflow file ✅
- **WHEN** `workflow-file` flag is set to custom value
- **THEN** use the specified filename for workflow state tracking

#### Scenario: Variable substitution in workflow file path ✅
- **WHEN** `workflow-file` flag contains variables like `{project-name}`, `{project-key}`, `{project-hash}`
- **THEN** substitute variables with actual project values before path resolution
- **AND** support patterns like `/tmp/.{project-hash}.yaml` or `{project-name}-workflow.yaml`

#### Scenario: Workflow file security validation ✅
- **WHEN** resolving workflow file path relative to client root
- **THEN** use existing ReadWriteSecurityPolicy to validate write permissions
- **AND** exclude system directories and unsafe temp paths per filesystem security modules
- **AND** return clear error if path validation fails

#### Scenario: Invalid workflow file configuration ✅
- **WHEN** `workflow-file` flag is set to invalid path
- **THEN** return error message identifying the flag name and invalid filename
- **AND** indicate that flag must be corrected for workflow tracking to work
- **AND** perform this validation before any agent requests

### Requirement: Flag Validation Registration ✅ IMPLEMENTED
The system SHALL support registration of flag-specific validators for semantic validation during flag setting operations.

#### Scenario: Validator registration ✅
- **WHEN** a module needs to validate specific flag values
- **THEN** register a validator function for that flag name
- **AND** validator function receives flag value and returns boolean validity

#### Scenario: Semantic validation on flag setting ✅
- **WHEN** setting a flag value through any flag setting operation
- **THEN** check if a validator is registered for that flag
- **AND** call the registered validator before setting the value
- **AND** raise ValidationError with clear message if validation fails

#### Scenario: Workflow flag semantic validation ✅
- **WHEN** setting `workflow` flag with list of phase names
- **THEN** validate each phase name is in the allowed set
- **AND** provide specific error message for invalid phase names
- **WHEN** setting `workflow-file` flag
- **THEN** validate path security and format requirements

### Requirement: Security Policy Consolidation
The system SHALL consolidate overlapping filesystem security implementations into a unified security policy class.

#### Scenario: Unified security validation
- **WHEN** validating workflow file paths
- **THEN** use consolidated security policy that combines ReadWriteSecurityPolicy, PathValidator, and system directory exclusions
- **AND** eliminate code duplication across filesystem security modules

### Requirement: Workflow Configuration ✅ IMPLEMENTED
The system SHALL support enhanced `workflow` project flag configuration with boolean or list values.

#### Scenario: Workflow tracking disabled ✅
- **WHEN** `workflow` flag is false (default)
- **THEN** disable all workflow tracking functionality

#### Scenario: Default workflow sequence ✅
- **WHEN** `workflow` flag is true
- **THEN** use default sequence: `discussion, planning, *implementation, check*, review*`

#### Scenario: Custom workflow sequence ✅
- **WHEN** `workflow` flag is a list of phase names
- **THEN** use the specified phases with transition controls

#### Scenario: Workflow transition controls ✅
- **WHEN** phase name has prefix asterisk (e.g., `*implementation`)
- **THEN** require explicit user confirmation before entering phase
- **WHEN** phase name has suffix asterisk (e.g., `check*`)
- **THEN** require explicit user confirmation to exit phase

### Requirement: Workflow State File Format
The system SHALL support a structured YAML format for the workflow state file.

#### Scenario: Valid workflow state structure
- **WHEN** workflow state file exists with valid YAML structure
- **THEN** parse phase, current issue, and issue queue successfully

#### Scenario: Workflow state validation
- **WHEN** workflow state file has invalid structure
- **THEN** provide clear error messages and fallback gracefully

### Requirement: Workflow Phase Configuration

The workflow configuration SHALL support `exploration` as an available phase without making it part of the standard ordered workflow sequence.

#### Scenario: Exploration is available but non-ordered
- **WHEN** workflow phases are configured
- **THEN** `exploration` is included in the available/default phase set
- **AND** it is not inserted into the standard ordered sequence of delivery phases

#### Scenario: Leaving exploration requires consent
- **WHEN** the current workflow phase is `exploration`
- **THEN** transitioning out of that phase requires explicit user consent

### Requirement: Onboarding Covers Workflow Preferences

The onboarding system SHALL support user choice over workflow behavior using a
defined set of onboarding-facing workflow modes that map to valid `workflow`
project flag values.

#### Scenario: User disables workflow during onboarding
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `none` or `unstructured`
- **THEN** onboarding maps that choice to `workflow: false`

#### Scenario: User selects structured workflow shorthand
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `structured`
- **THEN** onboarding maps that choice to `workflow: true`

#### Scenario: User selects simple workflow
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `simple`
- **THEN** onboarding maps that choice to `workflow: [discussion, implementation, exploration]`

#### Scenario: User selects developer workflow
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `developer`
- **THEN** onboarding maps that choice to `workflow: [discussion, implementation, review, exploration]`

#### Scenario: User selects full workflow
- **WHEN** onboarding presents workflow-related setup choices
- **AND** the user selects `full`
- **THEN** onboarding maps that choice to `workflow: [discussion, planning, implementation, check, review, exploration]`

#### Scenario: Full workflow is the explicit full-sequence option
- **WHEN** onboarding presents workflow-related setup choices
- **THEN** `structured` is available as the boolean shorthand for the standard
  enabled workflow
- **AND** `full` is available as the explicit onboarding option for the full
  ordered phase sequence
- **AND** both options map to server-valid workflow configurations

### Requirement: Exploration Remains Non-Linear In Workflow Variants

Workflow variants exposed during onboarding SHALL treat `exploration` as an
available exploratory mode rather than a normal ordered delivery phase.

#### Scenario: Exploration is available in all workflow-enabled variants
- **WHEN** onboarding presents any workflow-enabled choice
- **THEN** the resulting workflow configuration includes `exploration` as an
  available phase

#### Scenario: Exploration is not available when workflow is disabled
- **WHEN** onboarding maps the selected workflow choice to `workflow: false`
- **THEN** workflow tracking is disabled
- **AND** `exploration` is not presented as available through the workflow
  system

#### Scenario: Exploration is not treated as an ordered predecessor or successor
- **WHEN** onboarding describes or applies workflow variants that include
  `exploration`
- **THEN** it does not describe `exploration` as having a natural previous or
  next delivery phase
- **AND** it treats `exploration` as a mode for investigating approaches,
  testing alternatives, and often drafting OpenSpec proposals

#### Scenario: Exploration remains distinct from discussion
- **WHEN** onboarding explains workflow variants containing `exploration`
- **THEN** it distinguishes `exploration` from `discussion`
- **AND** it describes `discussion` as alignment-oriented
- **AND** it describes `exploration` as approach-oriented

