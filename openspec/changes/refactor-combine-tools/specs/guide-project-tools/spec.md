## MODIFIED Requirements

### Requirement: Unified Project Management Tool
The system SHALL provide a single `project` tool that accepts a discriminated union of action-specific argument classes.

#### Scenario: Tool uses existing argument classes
- **GIVEN** existing `ProjectGetArgs`, `ProjectSetArgs`, `ProjectListArgs`, `ProjectListOneArgs`, `ProjectCloneArgs` classes
- **WHEN** implementing the unified tool
- **THEN** use Pydantic discriminated union with `action` discriminator field
- **AND** each action maps to its existing Args class
- **AND** internal functions remain unchanged

#### Scenario: Get action
- **GIVEN** a current project exists
- **WHEN** agent calls tool with `ProjectGetArgs(action="get", verbose=True)`
- **THEN** dispatch to `internal_get_project()` with same args

#### Scenario: Set action
- **GIVEN** a project name is provided
- **WHEN** agent calls tool with `ProjectSetArgs(action="set", name="my-project")`
- **THEN** dispatch to `internal_set_project()` with same args

#### Scenario: List action (all projects)
- **GIVEN** multiple projects exist
- **WHEN** agent calls tool with `ProjectListArgs(action="list", verbose=False)`
- **THEN** dispatch to `internal_list_projects()` with same args

#### Scenario: All action (specific project info)
- **GIVEN** a project exists
- **WHEN** agent calls tool with `ProjectListOneArgs(action="all", name="my-project")`
- **THEN** dispatch to `internal_list_project()` with same args

#### Scenario: Clone action
- **GIVEN** source and target projects
- **WHEN** agent calls tool with `ProjectCloneArgs(action="clone", from_project="source", to_project="target")`
- **THEN** dispatch to `internal_clone_project()` with same args

### Requirement: Preserve Existing Internal Functions
The system SHALL keep all existing `internal_*_project*` functions unchanged.

#### Scenario: No logic changes
- **GIVEN** existing internal functions
- **WHEN** refactoring to unified tool
- **THEN** keep function signatures identical
- **AND** keep function implementations identical

## REMOVED Requirements

### Requirement: Separate Project Tool Entry Points
**Reason**: Consolidated into single tool with discriminated union
**Migration**: Agent discovers new tool signature automatically at initialization

The following tool entry points are removed (internal functions preserved):
- `get_project` → `project` with `ProjectGetArgs`
- `set_project` → `project` with `ProjectSetArgs`
- `list_projects` → `project` with `ProjectListArgs`
- `list_project` → `project` with `ProjectListOneArgs(action="all")`
- `clone_project` → `project` with `ProjectCloneArgs`
