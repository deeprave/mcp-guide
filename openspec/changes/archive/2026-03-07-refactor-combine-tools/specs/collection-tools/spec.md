## MODIFIED Requirements

### Requirement: Unified Collection Management Tool
The system SHALL provide a single `collection` tool that accepts a discriminated union of action-specific argument classes.

#### Scenario: Tool uses existing argument classes
- **GIVEN** existing `CollectionListArgs`, `CollectionAddArgs`, `CollectionRemoveArgs`, `CollectionChangeArgs`, `CollectionUpdateArgs` classes
- **WHEN** implementing the unified tool
- **THEN** use Pydantic discriminated union with `action` discriminator field
- **AND** each action maps to its existing Args class
- **AND** internal functions remain unchanged

#### Scenario: List action
- **GIVEN** a project with collections
- **WHEN** agent calls tool with `CollectionListArgs(action="list", verbose=True)`
- **THEN** dispatch to `internal_collection_list()` with same args

#### Scenario: Add action
- **GIVEN** a project configuration
- **WHEN** agent calls tool with `CollectionAddArgs(action="add", name="getting-started", ...)`
- **THEN** dispatch to `internal_collection_add()` with same args

#### Scenario: Remove action
- **GIVEN** a collection exists
- **WHEN** agent calls tool with `CollectionRemoveArgs(action="remove", name="docs")`
- **THEN** dispatch to `internal_collection_remove()` with same args

#### Scenario: Change action
- **GIVEN** a collection exists
- **WHEN** agent calls tool with `CollectionChangeArgs(action="change", name="docs", ...)`
- **THEN** dispatch to `internal_collection_change()` with same args

#### Scenario: Update action
- **GIVEN** a collection exists
- **WHEN** agent calls tool with `CollectionUpdateArgs(action="update", name="docs", ...)`
- **THEN** dispatch to `internal_collection_update()` with same args

### Requirement: Preserve Existing Internal Functions
The system SHALL keep all existing `internal_collection_*` functions unchanged.

#### Scenario: No logic changes
- **GIVEN** existing internal functions
- **WHEN** refactoring to unified tool
- **THEN** keep function signatures identical
- **AND** keep function implementations identical

## REMOVED Requirements

### Requirement: Separate Collection Tool Entry Points
**Reason**: Consolidated into single tool with discriminated union
**Migration**: Agent discovers new tool signature automatically at initialization

The following tool entry points are removed (internal functions preserved):
- `collection_list` → `collection` with `CollectionListArgs`
- `collection_add` → `collection` with `CollectionAddArgs`
- `collection_remove` → `collection` with `CollectionRemoveArgs`
- `collection_change` → `collection` with `CollectionChangeArgs`
- `collection_update` → `collection` with `CollectionUpdateArgs`
