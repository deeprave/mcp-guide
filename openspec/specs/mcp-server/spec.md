# mcp-server Specification

## Purpose
MCP server tools and functionality for project management and feature flags.
## Requirements
### Requirement: Name Validation System
The MCP server SHALL provide Unicode-aware validation for all naming throughout the system.

#### Scenario: Unicode character support
- **WHEN** validating project, category, collection, or flag names
- **THEN** accept Unicode alphanumeric characters (café, 项目, プロジェクト, проект)

#### Scenario: Problematic character rejection
- **WHEN** validating names containing spaces, slashes, or special characters
- **THEN** reject names with spaces, /, \, @, :, ;, ?, *, &, ! characters

#### Scenario: Consolidated validation pattern
- **WHEN** any component requires name validation
- **THEN** use unified Unicode-aware regex pattern from models.py

#### Scenario: Flag name specific rules
- **WHEN** validating feature flag names
- **THEN** use same Unicode pattern but maintain no-periods rule for future dot notation

### Requirement: list_flags Tool
The MCP server SHALL provide a list_flags tool for querying feature flag configurations.

#### Scenario: List global flags
- **WHEN** list_flags is invoked with project="*"
- **THEN** return all global feature flags

#### Scenario: List current project flags (active)
- **WHEN** list_flags is invoked with project=None and active=True
- **THEN** return merged global and current project flags

#### Scenario: List current project flags (project-only)
- **WHEN** list_flags is invoked with project=None and active=False
- **THEN** return only current project flags

#### Scenario: List specific project flags
- **WHEN** list_flags is invoked with project name
- **THEN** return flags for specified project based on active parameter

#### Scenario: Get specific flag value
- **WHEN** list_flags is invoked with feature_name parameter
- **THEN** return single flag value instead of dict

#### Scenario: No current project error
- **WHEN** list_flags requires current project but none exists
- **THEN** return no_project error

### Requirement: set_flag Tool
The MCP server SHALL provide a set_flag tool for modifying feature flag values.

#### Scenario: Set flag with default value
- **WHEN** set_flag is invoked with feature_name only
- **THEN** set flag value to True (default)

#### Scenario: Set flag with explicit value
- **WHEN** set_flag is invoked with feature_name and value
- **THEN** set flag to specified value

#### Scenario: Remove flag
- **WHEN** set_flag is invoked with value=None
- **THEN** remove flag from configuration

#### Scenario: Set global flag
- **WHEN** set_flag is invoked with project="*"
- **THEN** modify global feature flags

#### Scenario: Set current project flag
- **WHEN** set_flag is invoked with project=None
- **THEN** modify current project flags

#### Scenario: Immediate persistence
- **WHEN** set_flag successfully modifies configuration
- **THEN** immediately persist changes to disk

#### Scenario: Validation error
- **WHEN** set_flag receives invalid flag name or value
- **THEN** return validation error without modifying configuration

### Requirement: get_flag Tool
The MCP server SHALL provide a get_flag tool for retrieving individual feature flag values.

#### Scenario: Get flag with resolution
- **WHEN** get_flag is invoked with feature_name
- **THEN** return resolved value using project → global → None hierarchy

#### Scenario: Get global flag specifically
- **WHEN** get_flag is invoked with project="*"
- **THEN** return global flag value only (no resolution)

#### Scenario: Get current project context
- **WHEN** get_flag is invoked with project=None
- **THEN** use current project for resolution

#### Scenario: Flag not found
- **WHEN** get_flag cannot find flag in resolution hierarchy
- **THEN** return None value

### Requirement: Feature Flag Tool Integration
All feature flag tools SHALL integrate with existing MCP server patterns and error handling.

#### Scenario: Result pattern responses
- **WHEN** feature flag tool completes operation
- **THEN** return standardized Result pattern response

#### Scenario: Session management integration
- **WHEN** tool requires current project context
- **THEN** use session management for project access

#### Scenario: Configuration validation
- **WHEN** modifying feature flags
- **THEN** validate configuration before persistence

#### Scenario: Concurrent access protection
- **WHEN** multiple tools modify configuration simultaneously
- **THEN** use file locking to prevent conflicts

