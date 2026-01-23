# mcp-server Specification

## Purpose
MCP server tools and functionality for project management and feature flags.
## Requirements
### Requirement: First-Run Installation Check
The system SHALL check for configuration file on startup and trigger installation if missing.

#### Scenario: Configuration exists
- **WHEN** server starts and config file exists
- **THEN** server proceeds with normal startup
- **AND** no installation is triggered

#### Scenario: Configuration missing
- **WHEN** server starts and config file doesn't exist
- **THEN** automatic installation is triggered
- **AND** server stops after installation completes
- **AND** user is instructed to restart server

### Requirement: Manual Update Support
The system SHALL provide manual installer script for updating templates.

#### Scenario: Manual update via script
- **WHEN** user runs `mcp-install` command
- **THEN** installer runs in non-interactive mode by default
- **AND** existing files are updated using smart strategy
- **AND** identical files are skipped

### Requirement: Server Configuration Options
The system SHALL support command-line options for docroot and config directory.

#### Scenario: Override docroot on server startup
- **WHEN** server starts with -d or --docroot option
- **THEN** server uses specified docroot
- **AND** config file is updated if docroot differs

#### Scenario: Override config directory on server startup
- **WHEN** server starts with -c or --configdir option
- **THEN** server loads config from specified directory
- **AND** creates config there if it doesn't exist

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

### Requirement: Guide Prompt Support
The MCP server SHALL provide a `guide` prompt for direct content access without agent interpretation.

#### Scenario: Guide prompt with single argument
- **WHEN** user invokes `@guide category-name`
- **THEN** system calls get_content with category-name as argument
- **AND** returns content directly to user

#### Scenario: Guide prompt with multiple arguments
- **WHEN** user invokes `@guide lang/python advanced tutorial`
- **THEN** system processes first argument "lang/python" for MVP
- **AND** builds argv list: ["guide", "lang/python", "advanced", "tutorial"]
- **AND** reserves additional arguments for future click processing

#### Scenario: Guide prompt without arguments
- **WHEN** user invokes `@guide` with no arguments
- **THEN** system returns help message with usage examples
- **AND** does not error or crash

#### Scenario: Guide prompt argument parsing
- **WHEN** MCP client sends space-separated arguments
- **THEN** each argument maps to arg1, arg2, ..., argF parameters
- **AND** parsing stops at first None parameter
- **AND** builds clean argv list for processing

### Requirement: Prompt Registration
The MCP server SHALL register prompts during server initialization alongside tools.

#### Scenario: Server startup with prompts
- **WHEN** MCP server initializes
- **THEN** guide prompt is registered with FastMCP
- **AND** prompt uses direct function parameters (arg1-argF)
- **AND** prompt is available for client invocation

#### Scenario: Prompt schema availability
- **WHEN** agent queries available prompts
- **THEN** guide prompt schema shows 15 optional string parameters
- **AND** agents understand space-separated argument mapping

### Requirement: OpenSpec Feature Detection
The MCP server SHALL conditionally enable OpenSpec functionality based on feature flag configuration and project structure detection.

#### Scenario: Feature flag enabled with valid OpenSpec project
- **WHEN** feature flag "openspec-support" is enabled AND openspec/ directory exists AND openspec/project.md exists
- **THEN** OpenSpec tools and resources are available through MCP

#### Scenario: Feature flag disabled
- **WHEN** feature flag "openspec-support" is disabled
- **THEN** OpenSpec tools and resources are not available through MCP

#### Scenario: Missing OpenSpec structure
- **WHEN** feature flag "openspec-support" is enabled AND openspec/ directory does not exist
- **THEN** OpenSpec tools return appropriate error messages indicating missing OpenSpec project

### Requirement: OpenSpec Workflow Tools
The MCP server SHALL provide tools for OpenSpec spec-driven development workflows.

#### Scenario: List specifications
- **WHEN** list-specs tool is invoked
- **THEN** return all specifications from openspec/specs/ with domain names and descriptions

#### Scenario: List changes
- **WHEN** list-changes tool is invoked with optional status filter
- **THEN** return active changes from openspec/changes/ with metadata and status

#### Scenario: Get change details
- **WHEN** get-change tool is invoked with change-id
- **THEN** return complete change details including proposal, tasks, design, and spec deltas

#### Scenario: Get project context
- **WHEN** get-project-context tool is invoked
- **THEN** return project metadata from openspec/project.md including conventions and tech stack

#### Scenario: Validate change
- **WHEN** validate-change tool is invoked with change-id
- **THEN** delegate to openspec CLI validation and return results

#### Scenario: Show delta
- **WHEN** show-delta tool is invoked with change-id
- **THEN** return formatted spec delta showing ADDED/MODIFIED/REMOVED requirements

#### Scenario: Compare specifications
- **WHEN** compare-specs tool is invoked with spec domain and optional change-id
- **THEN** return diff between current spec and proposed changes

### Requirement: OpenSpec State Resources
The MCP server SHALL provide queryable resources for OpenSpec project state.

#### Scenario: Project resource query
- **WHEN** openspec://project resource is requested
- **THEN** return project metadata from openspec/project.md

#### Scenario: Specification resource query
- **WHEN** openspec://specs/{domain} resource is requested
- **THEN** return current specification for the specified domain

#### Scenario: Change resource query
- **WHEN** openspec://changes/{change-id} resource is requested
- **THEN** return change details and current status

#### Scenario: Agents resource query
- **WHEN** openspec://agents resource is requested
- **THEN** return AI assistant configuration from AGENTS.md

### Requirement: OpenSpec Guided Prompts
The MCP server SHALL provide pre-written prompts for OpenSpec workflows.

#### Scenario: Draft proposal prompt
- **WHEN** @openspec draft-proposal prompt is requested
- **THEN** return guidance for creating change proposals following OpenSpec conventions

#### Scenario: Review proposal prompt
- **WHEN** @openspec review-proposal prompt is requested
- **THEN** return checklist for proposal review and iteration

#### Scenario: Implementation tasks prompt
- **WHEN** @openspec implement-tasks prompt is requested
- **THEN** return workflow guidance for implementing from task lists

#### Scenario: Archive change prompt
- **WHEN** @openspec archive-change prompt is requested
- **THEN** return post-completion change archival workflow guidance

### Requirement: OpenSpec Command Response Formatting
The MCP server SHALL format OpenSpec CLI JSON responses into user-friendly markdown for display.

#### Scenario: Format status response
- **WHEN** `.openspec-status.json` is received via send_file_content
- **THEN** format as markdown with change name, schema, completion status, and artifact table
- **AND** return as user/information type

#### Scenario: Format changes list response
- **WHEN** `.openspec-changes.json` is received via send_file_content
- **THEN** format as markdown table with change names, status, tasks completed, and last modified
- **AND** return as user/information type

#### Scenario: Format show response
- **WHEN** `.openspec-show.json` is received via send_file_content
- **THEN** format as structured markdown with change details, artifacts, and metadata
- **AND** return as user/information type

#### Scenario: Handle formatting errors
- **WHEN** OpenSpec JSON response is malformed or missing expected fields
- **THEN** return error message with raw JSON for debugging
- **AND** log warning for investigation

#### Scenario: Format CLI error responses
- **WHEN** OpenSpec CLI returns error in JSON response (e.g., missing required options, invalid change name)
- **THEN** format error as user-friendly markdown with error message and available options/suggestions
- **AND** return as user/information type

