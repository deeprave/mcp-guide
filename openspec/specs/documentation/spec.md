## ADDED Requirements

### Requirement: Guide URI Documentation
The system SHALL provide user documentation for the `guide://` URI scheme.

#### Scenario: Content URI documentation
- **WHEN** a user reads the guide URI documentation
- **THEN** it describes content URIs (`guide://expression`, `guide://expression/pattern`)
- **AND** it describes command URIs (`guide://_command`, `guide://_command/args`, `guide://_command/args?key=value`)
- **AND** it documents the `read_resource` tool as a fallback for clients without native MCP resource support

#### Scenario: Codex-specific guidance
- **WHEN** a Codex user reads the guide URI documentation
- **THEN** it explains that `guide://` URIs are the primary method for executing commands in Codex
- **AND** it provides practical examples

### Requirement: Stored Document Documentation
The system SHALL provide user documentation for stored documents and document ingest.

#### Scenario: Ingest documentation
- **WHEN** a user reads the stored document documentation
- **THEN** it describes how to ingest documents from local files, direct content, and URLs
- **AND** it explains how stored documents integrate with content discovery
- **AND** it documents `category_list_files` source filtering (`files`, `stored`, or both)
- **AND** it documents `document_update` and `document_remove` tools

## MODIFIED Requirements

### Requirement: Setup Documentation
The system SHALL provide detailed setup and configuration documentation separate from README.

#### Scenario: Setup guide content
- **WHEN** setup documentation is accessed
- **THEN** it contains detailed installation instructions
- **AND** documents all configuration options
- **AND** includes transport mode setup guides
- **AND** covers Docker deployment
- **AND** lists environment variables
- **AND** includes troubleshooting section
- **AND** includes Codex agent configuration

#### Scenario: Instructive content
- **WHEN** reading setup documentation
- **THEN** content is instructive (how-to)
- **AND** includes practical examples
- **AND** provides step-by-step guidance

### Requirement: Documentation Cohesion
The system SHALL provide cohesive linking between all documentation.

#### Scenario: Cross-references
- **WHEN** navigating documentation
- **THEN** README links to setup docs
- **AND** setup docs link to user docs
- **AND** CHANGELOG links to relevant documentation
- **AND** documentation index links to guide URI and stored document pages
- **AND** all links are functional

#### Scenario: Navigation
- **WHEN** user needs specific information
- **THEN** documentation structure guides them clearly
- **AND** related content is easy to find
- **AND** no duplicate or conflicting information exists
