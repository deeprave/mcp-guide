## ADDED Requirements

### Requirement: Server Namespace Rename
The system SHALL rename the existing `system` namespace to `server` for clarity in client-server architecture.

#### Scenario: Server context access
- **WHEN** template accesses `{{server.os}}`
- **THEN** return server operating system information
- **AND** maintain all existing system context functionality

#### Scenario: Backward compatibility
- **WHEN** existing templates use `{{system.*}}` variables
- **THEN** templates must be updated to use `{{server.*}}`
- **AND** provide clear migration guidance

### Requirement: Client Context Collection
The system SHALL provide a mechanism to collect and integrate client-side context information.

#### Scenario: Client data parameter
- **WHEN** `build_template_context()` is called with client_data
- **THEN** integrate client data into template context
- **AND** prioritize client data in namespace layering

#### Scenario: Nested dictionary handling
- **WHEN** client data contains nested structures
- **THEN** properly flatten for template access
- **AND** maintain namespace organization

### Requirement: ClientContextTask System
The system SHALL provide a task-based system for collecting client context.

#### Scenario: Basic OS detection
- **WHEN** ClientContextTask requests basic OS info
- **THEN** generate appropriate template instruction
- **AND** handle client response via send_file_content tool

#### Scenario: Detailed context collection
- **WHEN** basic OS info is received
- **THEN** request detailed platform-specific context
- **AND** process structured JSON response

#### Scenario: Template-driven instructions
- **WHEN** generating client context requests
- **THEN** use templates from _common category
- **AND** provide OS-specific collection commands

### Requirement: Client-Server Data Exchange
The system SHALL establish clean boundaries for client-server context data exchange.

#### Scenario: Structured JSON format
- **WHEN** client sends context data
- **THEN** use standardized JSON structure
- **AND** validate data format before integration

#### Scenario: Event-based processing
- **WHEN** client context files are received
- **THEN** process via ClientContextTask event handling
- **AND** update template context cache

### Requirement: @task_init Decorator Pattern
The system SHALL provide a decorator-based auto-registration system for task managers.

#### Scenario: Automatic task manager registration
- **WHEN** a task manager class is decorated with @task_init
- **THEN** automatically register with appropriate decorator modules
- **AND** eliminate manual server.py initialization

#### Scenario: Import-time initialization
- **WHEN** task manager module is imported
- **THEN** @task_init decorator executes immediately
- **AND** task manager registers itself with system

#### Scenario: Consistent initialization pattern
- **WHEN** multiple task managers use @task_init
- **THEN** all follow same registration pattern
- **AND** maintain consistent lifecycle management

#### Scenario: Dependency order management
- **WHEN** task managers are imported before tools/prompts
- **THEN** managers are available when tools register
- **AND** prevent initialization order issues
