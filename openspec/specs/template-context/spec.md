# template-context Specification

## Purpose
Define values exposed to templates and their server, agent, and project namespaces.
## Requirements
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

### Requirement: OpenSpec Context Data
The template context system SHALL include OpenSpec project data when OpenSpec support is enabled.

#### Scenario: OpenSpec project metadata
- **WHEN** OpenSpec project is detected
- **THEN** context includes project name, description, and tech stack from openspec/project.md

#### Scenario: Active changes data
- **WHEN** OpenSpec project has active changes
- **THEN** context includes list of change IDs, titles, and status

#### Scenario: Specification domains
- **WHEN** OpenSpec project has specifications
- **THEN** context includes list of spec domains and descriptions

#### Scenario: Agent configuration
- **WHEN** AGENTS.md exists in OpenSpec project
- **THEN** context includes AI assistant configuration and conventions

### Requirement: Global OpenSpec state context
The template context system SHALL obtain OpenSpec CLI validation and version
state from the global `openspec-state` feature flag rather than the active
project entry.
Whether OpenSpec context is available for an active Project SHALL remain
controlled by that Project's `project_flags.openspec` setting.

#### Scenario: OpenSpec is disabled for the active project
- **WHEN** global OpenSpec CLI state is available but the active Project does not enable OpenSpec
- **THEN** the template context SHALL treat OpenSpec as disabled for that Project

#### Scenario: Render global OpenSpec state
- **WHEN** a template renders OpenSpec validation or CLI version information
- **THEN** it SHALL use the global `openspec-state.validated` and
  `openspec-state.version` values

#### Scenario: Project switch retains OpenSpec CLI state
- **WHEN** the active project changes on the same computer
- **THEN** OpenSpec CLI validation and version context SHALL remain derived from
  the same global state
- **AND** the project switch SHALL NOT trigger a version check solely because
  the project changed

### Requirement: On-demand OpenSpec changes context
The template context system SHALL obtain OpenSpec change data only when a
rendered feature requires that data. It SHALL evaluate that data in a dynamic
context layer on every render, reusing a valid per-session cached changes list
rather than issuing another client request.

#### Scenario: First change-data consumer
- **WHEN** an OpenSpec-enabled command or template requires changes data and
  no valid cached list exists
- **THEN** the system SHALL request `openspec list --json` once
- **AND** SHALL cache the received list for subsequent consumers

#### Scenario: Valid changes cache
- **WHEN** an OpenSpec-enabled command or template requires changes data and
  the cached list is within its TTL and matches the observed
  `openspec/changes` directory modification time
- **THEN** the system SHALL use the cached list
- **AND** SHALL NOT request another OpenSpec changes list

#### Scenario: Invalidated changes cache
- **WHEN** an OpenSpec-enabled command or template requires changes data and
  the cached list has expired or the observed `openspec/changes` directory
  modification time differs from the cached value
- **THEN** the system SHALL request a refreshed changes list
- **AND** SHALL replace the cached list and its cache metadata after receiving
  the response

#### Scenario: Forced refresh after a mutation
- **WHEN** a successful OpenSpec mutation directs the agent to
  `guide://_openspec/list?force`
- **THEN** the list command SHALL request a fresh directory listing and
  `openspec list --json` even when cached changes data remains valid

### Requirement: Prompt-aware template guidance
The template context SHALL suppress prompt-invocation guidance for agents whose prompt prefix is absent.

#### Scenario: Render for an agent without prompt support
- **WHEN** a template is rendered for an agent with `prompt_prefix=None`
- **THEN** the rendered content SHALL omit prompt invocation syntax

### Requirement: Dynamic authentication template context
Template rendering with a supplied session SHALL expose an `auth` mapping for
the current request with boolean `active`, `authenticated`, `user`, and `admin`
values. Rendering without a session SHALL omit the mapping.

For a template rendered during a current remote request, `active` SHALL be true
only when a provider is configured for that transport.
Template activity projects the presence of a provider decision for the current
request, including an unauthenticated decision. It is distinct from the
configured-provider check that enables tool enforcement. Session rendering
without a bound provider decision SHALL retain inactive, unrestricted template
predicates without disabling enforcement.
`authenticated`, `user`, and `admin` SHALL express access predicates, not raw
identity claims. When `active` is false, all three scope predicates SHALL be
true. With authentication active, `authenticated` SHALL mean that the caller
has `user` or `admin`; an additional capability scope alone SHALL NOT establish
authenticated state. `admin` true SHALL imply `authenticated` and `user` true. The context
SHALL expose no token, principal, provider configuration, or provider result
detail.

#### Scenario: Authentication is inactive
- **GIVEN** a session is supplied without a configured provider or on stdio
- **WHEN** a template is rendered with a session without a configured provider or on stdio
- **THEN** `auth.active` SHALL be false
- **AND** `auth.authenticated`, `auth.user`, and `auth.admin` SHALL be true

#### Scenario: Template rendering has no session
- **GIVEN** no session is supplied
- **WHEN** a template is rendered without a supplied session
- **THEN** its context SHALL have no `auth` mapping, even during an authenticated request

#### Scenario: Authenticated non-admin caller renders a template
- **GIVEN** the provider-backed caller is authenticated but lacks administrative access
- **WHEN** a provider-backed caller is authenticated but lacks administrative
  access
- **THEN** `auth.active` and `auth.authenticated` SHALL be true
- **AND** `auth.admin` SHALL be false
- **AND** `auth.user` SHALL be true and `auth.admin` SHALL be false

### Requirement: Request-safe scope projection
The `auth` mapping SHALL be calculated from current request decisions and
SHALL NOT be retained in a session-wide template-context cache. Changes in
caller authentication or provider policy SHALL not cause one caller's
availability values to be rendered for another caller.

#### Scenario: Consecutive callers have different access
- **GIVEN** two remote callers have different provider decisions
- **WHEN** two remote callers with different provider decisions render the same
  template in sequence
- **THEN** each rendering SHALL contain only the current caller's `auth`
  mapping
