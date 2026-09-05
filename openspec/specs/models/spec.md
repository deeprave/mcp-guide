# models Specification

## Purpose
TBD - created by archiving change config-session-management. Update Purpose after archive.
## Requirements
### Requirement: Pydantic Model Configuration
The system SHALL configure Pydantic models to ignore extra fields not defined in the model schema, improving resilience to hand-edited configurations and backward compatibility.

#### Scenario: Project model ignores extra fields
- **WHEN** a Project is instantiated with extra fields not in the schema
- **THEN** the model is created successfully and extra fields are silently ignored

#### Scenario: Category model ignores extra fields
- **WHEN** a Category is instantiated with extra fields not in the schema
- **THEN** the model is created successfully and extra fields are silently ignored

#### Scenario: Collection model ignores extra fields
- **WHEN** a Collection is instantiated with extra fields not in the schema
- **THEN** the model is created successfully and extra fields are silently ignored

#### Scenario: Config with deprecated fields loads successfully
- **WHEN** loading a YAML config containing deprecated fields from previous versions
- **THEN** the config loads successfully and deprecated fields are ignored

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

### Requirement: Project excludes legacy OpenSpec state
The `Project` model SHALL retain only project-level OpenSpec enablement and SHALL
not model machine-wide CLI state.

#### Scenario: Project serialisation after migration
- **WHEN** a Project is serialised after the migration
- **THEN** it SHALL NOT contain `openspec_validated` or `openspec_version`
- **AND** the Project's `project_flags.openspec` value SHALL remain serialised as
  the exclusive project-level enablement setting

### Requirement: Global Configuration Model
The configuration system SHALL support global feature flags with flexible value types.

#### Scenario: Global feature flags storage
- **WHEN** global configuration is loaded
- **THEN** include feature_flags dict with FeatureValue types

#### Scenario: Default empty feature flags
- **WHEN** new configuration is created
- **THEN** feature_flags defaults to empty dict

### Requirement: Project Configuration Model
The configuration system SHALL support project-specific feature flags with flexible value types.

#### Scenario: Project feature flags storage
- **WHEN** project configuration is loaded
- **THEN** include project_flags dict with FeatureValue types

#### Scenario: Default empty project flags
- **WHEN** new project is created
- **THEN** project_flags defaults to empty dict
### Requirement: Feature Flag Value Types
Feature flag values SHALL be restricted to supported types for consistency and validation.

The feature flag value model SHALL represent canonical boolean values as actual
booleans rather than boolean-looking strings.

The default feature flag contract SHALL support boolean and string values, while
structured values remain valid only for flags that explicitly opt into them
through registered validation and normalization.

#### Scenario: Boolean value remains typed
- **WHEN** a feature flag value is normalized to `true` or `false`
- **THEN** the feature flag value model SHALL store it as a boolean

#### Scenario: Arbitrary string remains typed as string
- **WHEN** a generic feature flag value is `"custom-mode"`
- **THEN** the feature flag value model SHALL store it as a string

#### Scenario: Structured value is preserved for registered flags
- **WHEN** a registered structured flag value is accepted by flag-specific
  validation
- **THEN** the feature flag value model SHALL preserve the structured value

### Requirement: Feature Flag Name Validation
Feature flag names SHALL follow project name validation rules with additional restrictions.

#### Scenario: Valid flag names
- **WHEN** flag name is validated
- **THEN** accept alphanumeric characters, hyphens, and underscores only

#### Scenario: Reject periods in flag names
- **WHEN** flag name contains periods
- **THEN** return validation error to avoid confusion with project syntax

#### Scenario: Name length validation
- **WHEN** flag name is validated
- **THEN** enforce same length restrictions as project names
### Requirement: Feature Flag Resolution
The system SHALL resolve feature flag values using project-specific → global → None hierarchy.

#### Scenario: Project flag takes precedence
- **WHEN** flag exists in both project and global configuration
- **THEN** return project-specific value

#### Scenario: Global flag fallback
- **WHEN** flag exists only in global configuration
- **THEN** return global value

#### Scenario: Flag not found
- **WHEN** flag does not exist in project or global configuration
- **THEN** return None

#### Scenario: Resolved boolean flag remains boolean
- **WHEN** a stored flag value has been normalized from `"true"` to boolean
  `true`
- **THEN** resolved flag access SHALL return the boolean value rather than the
  original string representation

### Requirement: Project Data Formatting
The system SHALL format project data without redundant information when the project name is already available in the parent context.

#### Scenario: Format project data for list output
- **WHEN** formatting project data where the name is the dictionary key
- **THEN** the output SHALL NOT include a redundant "project" field
- **AND** the output SHALL include "collections" and "categories" fields

#### Scenario: Format project data for single project
- **WHEN** formatting project data for a single project response
- **THEN** the output SHALL include "collections" and "categories" fields
- **AND** MAY include project name if not redundant with context

### Requirement: Non-empty profile collections
The system SHALL reject a profile collection that does not declare at least one category or expression.

#### Scenario: Reject empty collection
- **WHEN** a profile containing a collection with an empty category list is loaded
- **THEN** profile validation SHALL fail with a descriptive error

#### Scenario: Apply complete default collection
- **WHEN** the default profile is applied to a new project
- **THEN** it SHALL include a code-review collection that resolves the review guidance

### Requirement: Baseline profile resources
The system SHALL configure every resource referenced by an unconditional baseline command to resolve to non-empty rendered content in a newly configured default project.

#### Scenario: Resolve baseline review and check guidance
- **WHEN** the default profile is applied to a new project
- **THEN** the `code-review`, `review`, and `checks` resources SHALL each resolve to non-empty rendered content
