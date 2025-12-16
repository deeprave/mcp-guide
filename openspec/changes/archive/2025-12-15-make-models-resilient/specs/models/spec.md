# Capability: Models

## MODIFIED Requirements

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

#### Scenario: Supported value types
- **WHEN** feature flag value is set
- **THEN** accept only bool, str, list[str], or dict[str, str] types

#### Scenario: Type validation
- **WHEN** invalid value type is provided
- **THEN** return validation error with supported types

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
