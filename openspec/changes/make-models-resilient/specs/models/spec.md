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
