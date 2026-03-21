## ADDED Requirements

### Requirement: System Template Directory
The template system SHALL support a `_system/` directory for system-level templates that are not tied to specific features.

#### Scenario: System templates rendered
- **WHEN** a system template is requested by name (e.g., `startup`, `update`, `export`)
- **THEN** the system locates and renders the template from `_system/` directory

#### Scenario: System templates support full Mustache features
- **WHEN** a system template is rendered
- **THEN** it supports conditionals, sections, partials, and all standard Mustache features
