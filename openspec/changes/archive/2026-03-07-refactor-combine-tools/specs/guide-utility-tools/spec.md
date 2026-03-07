## MODIFIED Requirements

### Requirement: Unified Profile Management Tool
The system SHALL provide a single `profile` tool that accepts a discriminated union of action-specific argument classes.

#### Scenario: Tool uses existing argument classes
- **GIVEN** existing `ProfileListArgs`, `ProfileShowArgs`, `ProfileUseArgs` classes
- **WHEN** implementing the unified tool
- **THEN** use Pydantic discriminated union with `action` discriminator field
- **AND** each action maps to its existing Args class
- **AND** internal functions remain unchanged

#### Scenario: List action
- **GIVEN** available profiles exist
- **WHEN** agent calls tool with `ProfileListArgs(action="list")`
- **THEN** dispatch to `internal_list_profiles()` with same args

#### Scenario: Show action
- **GIVEN** a profile exists
- **WHEN** agent calls tool with `ProfileShowArgs(action="show", profile="python")`
- **THEN** dispatch to `internal_show_profile()` with same args

#### Scenario: Use action
- **GIVEN** a profile exists and project is active
- **WHEN** agent calls tool with `ProfileUseArgs(action="use", profile="python")`
- **THEN** dispatch to `internal_use_project_profile()` with same args

### Requirement: Preserve Existing Internal Functions
The system SHALL keep all existing `internal_*_profile*` functions unchanged.

#### Scenario: No logic changes
- **GIVEN** existing internal functions
- **WHEN** refactoring to unified tool
- **THEN** keep function signatures identical
- **AND** keep function implementations identical

## REMOVED Requirements

### Requirement: Separate Profile Tool Entry Points
**Reason**: Consolidated into single tool with discriminated union
**Migration**: Agent discovers new tool signature automatically at initialization

The following tool entry points are removed (internal functions preserved):
- `list_profiles` → `profile` with `ProfileListArgs`
- `show_profile` → `profile` with `ProfileShowArgs`
- `use_project_profile` → `profile` with `ProfileUseArgs`
