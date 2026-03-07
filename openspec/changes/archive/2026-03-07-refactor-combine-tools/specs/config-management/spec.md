## MODIFIED Requirements

### Requirement: Unified Feature Flag Management Tool
The system SHALL provide a single `flag` tool that accepts a discriminated union of action-specific argument classes with a `type` field to distinguish project vs global flags.

#### Scenario: Tool uses existing argument classes with type field
- **GIVEN** existing flag management Args classes
- **WHEN** implementing the unified tool
- **THEN** add `type` field (Literal["project"] | None) to each Args class
- **AND** use Pydantic discriminated union with `action` discriminator
- **AND** `type="project"` operates on project flags, `type=None` operates on global flags

#### Scenario: List action with type
- **GIVEN** project and global flags exist
- **WHEN** agent calls tool with `FlagListArgs(action="list", type="project")`
- **THEN** dispatch to `internal_list_project_flags()` with same args
- **WHEN** agent calls tool with `FlagListArgs(action="list", type=None)`
- **THEN** dispatch to `internal_list_feature_flags()` with same args

#### Scenario: Get action with type
- **GIVEN** flags exist
- **WHEN** agent calls tool with `FlagGetArgs(action="get", type="project", feature_name="workflow")`
- **THEN** dispatch to `internal_get_project_flag()` with same args
- **WHEN** agent calls tool with `FlagGetArgs(action="get", type=None, feature_name="content-style")`
- **THEN** dispatch to `internal_get_feature_flag()` with same args

#### Scenario: Set action with type
- **GIVEN** a project or global context
- **WHEN** agent calls tool with `FlagSetArgs(action="set", type="project", feature_name="workflow", value=True)`
- **THEN** dispatch to `internal_set_project_flag()` with same args
- **WHEN** agent calls tool with `FlagSetArgs(action="set", type=None, feature_name="content-style", value="mime")`
- **THEN** dispatch to `internal_set_feature_flag()` with same args

### Requirement: Preserve Existing Internal Functions
The system SHALL keep all existing `internal_*_flag` and `internal_*_flags` functions unchanged.

#### Scenario: No logic changes
- **GIVEN** existing internal functions
- **WHEN** refactoring to unified tool
- **THEN** keep function signatures identical
- **AND** keep function implementations identical

## REMOVED Requirements

### Requirement: Separate Flag Tool Entry Points
**Reason**: Consolidated into single tool with discriminated union and type field
**Migration**: Agent discovers new tool signature automatically at initialization

The following tool entry points are removed (internal functions preserved):
- `list_project_flags` → `flag` with `FlagListArgs(type="project")`
- `get_project_flag` → `flag` with `FlagGetArgs(type="project")`
- `set_project_flag` → `flag` with `FlagSetArgs(type="project")`
- `list_feature_flags` → `flag` with `FlagListArgs(type=None)`
- `get_feature_flag` → `flag` with `FlagGetArgs(type=None)`
- `set_feature_flag` → `flag` with `FlagSetArgs(type=None)`
