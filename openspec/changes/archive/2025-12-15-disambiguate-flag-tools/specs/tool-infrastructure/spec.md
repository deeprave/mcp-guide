# tool-infrastructure Specification Delta

## ADDED Requirements

### Requirement: Project Flag Tool Naming
The system SHALL provide explicitly named tools for project flag operations.

#### Scenario: Project flag tool registration
- **WHEN** MCP server initializes
- **THEN** `set_project_flag` tool is registered for setting project flags
- **AND** `get_project_flag` tool is registered for getting project flags with resolution
- **AND** `list_project_flags` tool is registered for listing project flags

#### Scenario: Project flag resolution hierarchy
- **WHEN** `get_project_flag` or `list_project_flags` is called
- **THEN** project flags override global flags in resolution
- **AND** global flags provide defaults when project flags not set
- **AND** resolution hierarchy is preserved from original implementation

### Requirement: Global Flag Tool Naming
The system SHALL provide explicitly named tools for global flag operations.

#### Scenario: Global flag tool registration
- **WHEN** MCP server initializes
- **THEN** `set_feature_flag` tool is registered for setting global flags
- **AND** `get_feature_flag` tool is registered for getting global flags only
- **AND** `list_feature_flags` tool is registered for listing global flags only

#### Scenario: Global flag isolation
- **WHEN** global flag tools are called
- **THEN** operations work exclusively with `session.feature_flags()`
- **AND** no resolution hierarchy or project flag merging occurs
- **AND** operations are isolated to global scope only

## MODIFIED Requirements

### Requirement: Tool Documentation Convention
The system SHALL enforce documentation conventions for tools.

#### Scenario: Undecorated name in documentation
- **WHEN** tool documentation is written
- **THEN** undecorated tool name is used
- **AND** prefix is not mentioned in documentation
- **AND** prefix is treated as implementation detail
- **AND** flag tools use explicit scope naming (project_flag vs feature_flag)

## REMOVED Requirements

None - this change is purely additive with renames for clarity.
