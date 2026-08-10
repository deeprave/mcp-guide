# template-resource-integrity Specification

## Purpose

Keep static bundled resource references aligned with available rendered content.

## Requirements

### Requirement: Static bundled resource references
The system SHALL keep each literal bundled `{{#resource}}...{{/resource}}` target aligned with a real bundled document, collection, category, or command that produces non-empty output when its owning profile or feature is enabled.

#### Scenario: Validate a profile-dependent resource reference
- **WHEN** a bundled template contains a literal resource reference whose content is provided by an optional profile or feature
- **THEN** validation SHALL resolve that reference with the owning profile or feature enabled
- **AND** SHALL confirm that its rendered output is non-empty

#### Scenario: Exclude runtime-configured resource targets
- **WHEN** a bundled template references a resource through a runtime-configured value
- **THEN** static validation SHALL not require that arbitrary value to resolve in the default profile
