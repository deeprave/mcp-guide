# models Specification

## Purpose
TBD - created by archiving change config-session-management. Update Purpose after archive.
## Requirements
### Requirement: Immutable Project Model
The system SHALL provide an immutable Project model with functional updates.

#### Scenario: Project creation
- WHEN a Project is created with name, categories, and collections
- THEN the Project instance is frozen (immutable)
- AND all fields are validated by Pydantic
- AND timestamps are automatically set

#### Scenario: Functional updates
- WHEN a category is added via `project.with_category(category)`
- THEN a new Project instance is returned
- AND the original Project instance is unchanged
- AND the new instance includes the added category

### Requirement: Category Model
The system SHALL provide a Category model with name, directory, and patterns.

#### Scenario: Category validation
- WHEN a Category is created
- THEN name is validated (alphanumeric, hyphens, underscores)
- AND directory path is validated
- AND patterns list is validated (list of strings)

### Requirement: Collection Model
The system SHALL provide a Collection model grouping related categories.

#### Scenario: Collection creation
- WHEN a Collection is created with name and category list
- THEN name is validated
- AND category names are validated
- AND description is optional

### Requirement: SessionState Model
The system SHALL provide a mutable SessionState model for runtime state.

#### Scenario: State management
- WHEN SessionState is created
- THEN it contains mutable runtime data
- AND it is NOT frozen (allows mutation)
- AND it tracks current working directory, cache, etc.

### Requirement: YAML Serialization
The system SHALL support bidirectional YAML serialization for Project model.

#### Scenario: Serialization
- WHEN a Project is serialized to YAML
- THEN all fields are included
- AND nested models (categories, collections) are serialized
- AND timestamps are in ISO format

#### Scenario: Deserialization
- WHEN YAML is deserialized to Project
- THEN all fields are validated
- AND nested models are reconstructed
- AND invalid data raises validation errors

