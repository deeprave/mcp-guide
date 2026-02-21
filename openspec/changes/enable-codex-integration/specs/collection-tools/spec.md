## ADDED Requirements

### Requirement: Collection Name Underscore Validation

Collection names SHALL NOT start with underscore character.

The underscore prefix SHALL be reserved for system use.

Validation SHALL occur in `collection_add` and `collection_change` tools.

#### Scenario: Add collection with underscore prefix
- **WHEN** user calls `collection_add` with name starting with underscore
- **THEN** tool returns validation error "Collection names cannot start with underscore (reserved for system use)"

#### Scenario: Rename collection to underscore prefix
- **WHEN** user calls `collection_change` with new_name starting with underscore
- **THEN** tool returns validation error "Collection names cannot start with underscore (reserved for system use)"

#### Scenario: Valid collection name
- **WHEN** user calls `collection_add` with name not starting with underscore
- **THEN** validation passes and collection is created

### Requirement: Consistency with Category Validation

Collection underscore validation SHALL match existing category underscore validation.

Error messages SHALL be consistent between category and collection tools.

#### Scenario: Consistent error messages
- **WHEN** category or collection name starts with underscore
- **THEN** error message format is "X names cannot start with underscore (reserved for system use)"

#### Scenario: Consistent validation logic
- **WHEN** validating category or collection names
- **THEN** both use `name.startswith("_")` check
