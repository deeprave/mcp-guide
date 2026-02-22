## MODIFIED Requirements

### Requirement: Unified Category Management Tool
The system SHALL provide a single `category` tool that accepts a discriminated union of action-specific argument classes.

#### Scenario: Tool uses existing argument classes
- **GIVEN** existing `CategoryListArgs`, `CategoryAddArgs`, `CategoryRemoveArgs`, `CategoryChangeArgs`, `CategoryUpdateArgs`, `CategoryListFilesArgs` classes
- **WHEN** implementing the unified tool
- **THEN** use Pydantic discriminated union with `action` discriminator field
- **AND** each action maps to its existing Args class
- **AND** internal functions remain unchanged

#### Scenario: List action
- **GIVEN** a project with categories
- **WHEN** agent calls tool with `CategoryListArgs(action="list", verbose=True)`
- **THEN** dispatch to `internal_category_list()` with same args
- **AND** return same result as current `category_list` tool

#### Scenario: Add action
- **GIVEN** a project configuration
- **WHEN** agent calls tool with `CategoryAddArgs(action="add", name="docs", ...)`
- **THEN** dispatch to `internal_category_add()` with same args
- **AND** return same result as current `category_add` tool

#### Scenario: Remove action
- **GIVEN** a category exists
- **WHEN** agent calls tool with `CategoryRemoveArgs(action="remove", name="docs")`
- **THEN** dispatch to `internal_category_remove()` with same args

#### Scenario: Change action
- **GIVEN** a category exists
- **WHEN** agent calls tool with `CategoryChangeArgs(action="change", name="docs", ...)`
- **THEN** dispatch to `internal_category_change()` with same args

#### Scenario: Update action
- **GIVEN** a category exists
- **WHEN** agent calls tool with `CategoryUpdateArgs(action="update", name="docs", ...)`
- **THEN** dispatch to `internal_category_update()` with same args

#### Scenario: Files action
- **GIVEN** a category exists
- **WHEN** agent calls tool with `CategoryListFilesArgs(action="files", name="docs")`
- **THEN** dispatch to `internal_category_list_files()` with same args

#### Scenario: Pydantic validates action
- **GIVEN** any request
- **WHEN** agent provides invalid action value
- **THEN** Pydantic discriminated union validation rejects automatically

### Requirement: Preserve Existing Internal Functions
The system SHALL keep all existing `internal_category_*` functions unchanged.

#### Scenario: No logic changes
- **GIVEN** existing internal functions
- **WHEN** refactoring to unified tool
- **THEN** keep function signatures identical
- **AND** keep function implementations identical
- **AND** only change is the single entry point dispatcher

## REMOVED Requirements

### Requirement: Separate Category Tool Entry Points
**Reason**: Consolidated into single tool with discriminated union
**Migration**: Agent discovers new tool signature automatically at initialization

The following tool entry points are removed (internal functions preserved):
- `category_list` → `category` with `CategoryListArgs`
- `category_add` → `category` with `CategoryAddArgs`
- `category_remove` → `category` with `CategoryRemoveArgs`
- `category_change` → `category` with `CategoryChangeArgs`
- `category_update` → `category` with `CategoryUpdateArgs`
- `category_list_files` → `category` with `CategoryListFilesArgs`
