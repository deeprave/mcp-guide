# Guide Project Tools Specification Changes

## MODIFIED Requirements

### Requirement: Project Information Retrieval
The `guide_get_project` tool SHALL return complete project configuration including categories, collections, and resolved project flags.

#### Scenario: Get complete project configuration
- GIVEN a project with categories, collections, and flags configured
- WHEN `guide_get_project(verbose=true)` is called
- THEN the response SHALL include:
  - Project name
  - Categories with their configuration
  - Collections with their configuration
  - Resolved project flags (global + project-specific)

#### Scenario: Get basic project information
- GIVEN a project configuration
- WHEN `guide_get_project(verbose=false)` is called
- THEN the response SHALL include project name and basic structure
- AND flags MAY be omitted for brevity

#### Scenario: Flag resolution
- GIVEN global feature flags and project-specific flags
- WHEN project flags are requested
- THEN the response SHALL include fully resolved flags
- AND project-specific flags SHALL override global flags where conflicts exist

### Requirement: Response Structure
The project information response SHALL include a `flags` field containing the resolved flag values as key-value pairs.

#### Scenario: Flags field format
- GIVEN resolved project flags
- WHEN flags are included in response
- THEN flags SHALL be formatted as `{"flag_name": boolean_value}`
- AND all flag values SHALL be resolved to their final boolean state
