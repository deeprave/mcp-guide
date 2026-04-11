## MODIFIED Requirements

### Requirement: Project Configuration Structure

The project configuration and default profile SHALL support a default `policy` category for optional steering documents.

#### Scenario: Default profile includes policy category
- **WHEN** the default profile is applied to a project
- **THEN** a `policy` category is available by default
- **AND** that category is intended for optional selectable policy documents

### Requirement: Policy Selection Uses Existing Configuration Concepts

The system SHALL represent policy choices using existing project configuration concepts rather than a separate policy object model.

#### Scenario: Policy selection is composed through normal configuration
- **WHEN** a project enables a set of policy choices
- **THEN** those choices are represented through categories, collections, profiles, or related project configuration
- **AND** no separate standalone policy storage model is required
