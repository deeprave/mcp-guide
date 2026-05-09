## MODIFIED Requirements

### Requirement: Feature Flag Value Types
Feature flag values SHALL be restricted to supported types for consistency and validation.

The default supported value types for generic feature flags SHALL be boolean and
string values only.

Structured values such as `list[str]` and `dict[str, str | list[str]]` SHALL be
accepted only for flags that explicitly register a validator and normaliser that
support those shapes.

#### Scenario: Supported default value types
- **WHEN** a generic feature flag value is set
- **THEN** accept only boolean or string values by default

#### Scenario: Registered structured flag value
- **WHEN** a built-in flag with a registered validator is set to its supported
  structured value
- **THEN** the configuration system SHALL accept the value
- **AND** it SHALL use the registered flag-specific behavior

#### Scenario: Unsupported generic structured value
- **WHEN** a generic feature flag is set to a list or dictionary value without a
  registered structured validator
- **THEN** return validation error with the supported default types

### Requirement: Project Configuration Model
The configuration system SHALL support project-specific feature flags with flexible value types.

#### Scenario: Project feature flags storage
- **WHEN** project configuration is loaded
- **THEN** include project_flags dict with FeatureValue types

#### Scenario: Default empty project flags
- **WHEN** new project is created
- **THEN** project_flags defaults to empty dict

#### Scenario: Project flag normalization before storage
- **WHEN** a project flag is set through the supported feature flag APIs
- **THEN** default or registered normalization SHALL run before the value is
  stored in project configuration
- **AND** canonical boolean values SHALL be persisted as booleans

### Requirement: Global Configuration Model
The configuration system SHALL support global feature flags with flexible value types.

#### Scenario: Global feature flags storage
- **WHEN** global configuration is loaded
- **THEN** include feature_flags dict with FeatureValue types

#### Scenario: Default empty feature flags
- **WHEN** new configuration is created
- **THEN** feature_flags defaults to empty dict

#### Scenario: Global flag normalization before storage
- **WHEN** a global feature flag is set through the supported feature flag APIs
- **THEN** default or registered normalization SHALL run before the value is
- stored in global configuration
- **AND** canonical boolean values SHALL be persisted as booleans

