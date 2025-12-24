# openspec-filesystem-integration Specification

## Purpose

Integrates filesystem interaction capabilities into OpenSpec tools, enabling dynamic discovery and validation of change proposals through agent-server filesystem collaboration.

## MODIFIED Requirements

### Requirement: OpenSpec Change Discovery
The system SHALL discover OpenSpec changes using filesystem interaction instead of static resources.

#### Scenario: List active changes dynamically
- **WHEN** list_changes is called
- **THEN** uses FilesystemBridge.list_directory("openspec/changes/")
- **AND** discovers all change directories dynamically
- **AND** filters out archived changes
- **AND** returns list of active change names

#### Scenario: Cache directory listings
- **WHEN** list_changes is called multiple times
- **THEN** uses cached directory listing if valid
- **AND** avoids redundant sampling requests
- **AND** invalidates cache when changes detected

#### Scenario: Detect new changes
- **WHEN** new change is created after cache
- **THEN** cache invalidation detects new change
- **AND** fresh directory listing includes new change
- **AND** change appears in list_changes result

### Requirement: OpenSpec File Content Access
The system SHALL read OpenSpec files using filesystem interaction.

#### Scenario: Read proposal file
- **WHEN** show_change needs to display proposal
- **THEN** uses FilesystemBridge.read_file("openspec/changes/{change}/proposal.md")
- **AND** returns proposal content from cache or agent
- **AND** preserves markdown formatting

#### Scenario: Read tasks file
- **WHEN** show_change needs to display tasks
- **THEN** uses FilesystemBridge.read_file("openspec/changes/{change}/tasks.md")
- **AND** parses task completion status
- **AND** returns structured task information

#### Scenario: Read spec deltas
- **WHEN** show_change needs to display specs
- **THEN** lists all specs in changes/{change}/specs/
- **AND** reads each spec.md file
- **AND** returns combined spec content

#### Scenario: Handle missing files
- **WHEN** expected file does not exist
- **THEN** FilesystemBridge returns file not found error
- **AND** tool provides clear error message
- **AND** suggests valid file structure

### Requirement: OpenSpec Validation
The system SHALL validate OpenSpec changes using filesystem interaction.

#### Scenario: Validate proposal structure
- **WHEN** validate_change is called
- **THEN** reads proposal.md via filesystem interaction
- **AND** validates required sections (Why, What Changes)
- **AND** returns validation errors if sections missing

#### Scenario: Validate spec formatting
- **WHEN** validate_change checks specs
- **THEN** lists all specs in change directory
- **AND** reads each spec file
- **AND** validates requirement and scenario structure
- **AND** returns formatting errors with line numbers

#### Scenario: Validate tasks structure
- **WHEN** validate_change checks tasks
- **THEN** reads tasks.md via filesystem interaction
- **AND** validates task checklist format
- **AND** validates required phases (Planning, Implementation, Check, Archive)
- **AND** returns validation errors with suggestions

### Requirement: Interactive Change Management
The system SHALL enable interactive change workflows using filesystem interaction.

#### Scenario: Real-time task tracking
- **WHEN** agent updates task completion in tasks.md
- **THEN** cache invalidation detects file change
- **AND** fresh read shows updated task status
- **AND** progress statistics reflect current state

#### Scenario: Dynamic spec updates
- **WHEN** agent modifies spec files
- **THEN** cache invalidation detects changes
- **AND** validation reflects current spec content
- **AND** agent receives immediate feedback

#### Scenario: Change completion detection
- **WHEN** all tasks marked complete
- **THEN** filesystem reads detect completion
- **AND** tool provides archive readiness check
- **AND** prompts agent for user approval

## ADDED Requirements

### Requirement: OpenSpec Cache Management
The system SHALL manage cache for OpenSpec file operations.

#### Scenario: Warm cache on project load
- **WHEN** project is initialized
- **THEN** preloads common OpenSpec files
- **AND** caches project.md and active changes
- **AND** improves first-operation performance

#### Scenario: Invalidate cache on archive
- **WHEN** change is archived
- **THEN** invalidates all cache entries for that change
- **AND** invalidates change list cache
- **AND** ensures next listing shows updated state

#### Scenario: Cache statistics reporting
- **WHEN** OpenSpec operations complete
- **THEN** includes cache statistics in results
- **AND** reports cache hits and misses
- **AND** helps optimize caching strategy

### Requirement: OpenSpec Security Configuration
The system SHALL configure filesystem security for OpenSpec operations.

#### Scenario: Default OpenSpec allowed paths
- **WHEN** SecurityPolicy is initialized
- **THEN** includes openspec/ in allowed paths by default
- **AND** includes .adr/ for ADR integration
- **AND** restricts access to OpenSpec directories only

#### Scenario: Reject access outside OpenSpec
- **WHEN** operation attempts to access non-OpenSpec files
- **THEN** SecurityPolicy rejects operation
- **AND** returns clear security error
- **AND** suggests valid paths

### Requirement: OpenSpec Error Handling
The system SHALL provide clear error messages for OpenSpec filesystem operations.

#### Scenario: Missing change directory
- **WHEN** change directory does not exist
- **THEN** returns user-friendly error
- **AND** suggests running openspec list to see available changes
- **AND** provides example of valid change names

#### Scenario: Malformed proposal
- **WHEN** proposal.md has invalid format
- **THEN** validation returns specific errors
- **AND** indicates line numbers where possible
- **AND** provides correction examples

#### Scenario: Filesystem unavailable
- **WHEN** agent does not support sampling
- **THEN** returns clear error about requirement
- **AND** suggests alternative workflows (manual file provision)
- **AND** documents sampling requirement

### Requirement: Backward Compatibility
The system SHALL maintain backward compatibility with non-filesystem OpenSpec access.

#### Scenario: Fallback to resources
- **WHEN** filesystem interaction unavailable
- **THEN** attempts to use MCP resources if available
- **AND** logs warning about limited functionality
- **AND** continues with available data

#### Scenario: Manual file provision
- **WHEN** neither filesystem nor resources available
- **THEN** provides clear instructions for manual operation
- **AND** suggests pasting file contents
- **AND** maintains core functionality with manual input