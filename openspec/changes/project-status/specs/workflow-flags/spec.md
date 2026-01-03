## ADDED Requirements

### Requirement: Workflow File Configuration
The system SHALL support a configurable workflow state file via the `workflow-file` project flag with variable substitution.

#### Scenario: Default workflow file
- **WHEN** `workflow-file` flag is not set
- **THEN** use `.guide.yaml` as the default workflow state file

#### Scenario: Custom workflow file
- **WHEN** `workflow-file` flag is set to custom value
- **THEN** use the specified filename for workflow state tracking

#### Scenario: Variable substitution in workflow file path
- **WHEN** `workflow-file` flag contains variables like `{project-name}`, `{project-key}`, `{project-hash}`
- **THEN** substitute variables with actual project values before path resolution
- **AND** support patterns like `/tmp/.{project-hash}.yaml` or `{project-name}-workflow.yaml`

#### Scenario: Workflow file security validation
- **WHEN** resolving workflow file path relative to client root
- **THEN** use existing ReadWriteSecurityPolicy to validate write permissions
- **AND** exclude system directories and unsafe temp paths per filesystem security modules
- **AND** return clear error if path validation fails

#### Scenario: Invalid workflow file configuration
- **WHEN** `workflow-file` flag is set to invalid path
- **THEN** return error message identifying the flag name and invalid filename
- **AND** indicate that flag must be corrected for workflow tracking to work
- **AND** perform this validation before any agent requests

### Requirement: Security Policy Consolidation
The system SHOULD consolidate overlapping filesystem security implementations into a unified security policy class.

#### Scenario: Unified security validation
- **WHEN** validating workflow file paths
- **THEN** use consolidated security policy that combines ReadWriteSecurityPolicy, PathValidator, and system directory exclusions
- **AND** eliminate code duplication across filesystem security modules

### Requirement: Workflow Configuration
The system SHALL support enhanced `workflow` project flag configuration with boolean or list values.

#### Scenario: Workflow tracking disabled
- **WHEN** `workflow` flag is false (default)
- **THEN** disable all workflow tracking functionality

#### Scenario: Default workflow sequence
- **WHEN** `workflow` flag is true
- **THEN** use default sequence: `discussion, planning, *implementation, check*, review*`

#### Scenario: Custom workflow sequence
- **WHEN** `workflow` flag is a list of phase names
- **THEN** use the specified phases with transition controls

#### Scenario: Workflow transition controls
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
