## ADDED Requirements

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
