# collection-tools Spec Delta

## MODIFIED Requirements

### Requirement: Dictionary-Based Collection Operations

All collection tools SHALL use dictionary-based operations for improved performance and automatic duplicate prevention.

**Lookup Operations:**
- Collection existence: `name in project.collections` (O(1))
- Collection retrieval: `project.collections[name]` (O(1))
- Collection iteration: `project.collections.values()` or `.items()`

**Modification Operations:**
- Add collection: `project.collections[name] = collection`
- Remove collection: `del project.collections[name]`
- Update collection: `project.collections[name] = updated_collection`

#### Scenario: Fast duplicate detection
- **WHEN** checking if collection already exists
- **THEN** use `name in project.collections` instead of linear search

#### Scenario: Direct collection access
- **WHEN** retrieving collection by name
- **THEN** use `project.collections[name]` for immediate access

#### Scenario: Collection not found handling
- **WHEN** accessing non-existent collection
- **THEN** catch `KeyError` and return "not_found" error

### Requirement: Simplified Validation Logic

Collection tools SHALL use simplified validation logic enabled by dictionary-based storage.

**Duplicate Detection:**
- Remove manual duplicate checking loops
- Rely on dictionary key uniqueness
- Use `KeyError` exceptions for not-found cases

**Performance Improvements:**
- O(1) collection lookups replace O(n) linear searches
- Faster "already exists" validation
- Reduced complexity in tool implementations

#### Scenario: Add collection duplicate check
- **WHEN** adding collection with existing name
- **THEN** check `name in project.collections` before addition

#### Scenario: Remove collection validation
- **WHEN** removing collection
- **THEN** verify existence with `name in project.collections`

#### Scenario: Change collection validation
- **WHEN** changing collection name
- **THEN** check new name not in `project.collections` (except current)
