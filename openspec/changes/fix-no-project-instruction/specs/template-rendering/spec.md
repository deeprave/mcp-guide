## ADDED Requirements

### Requirement: Unbound-session template rendering
The system SHALL support rendering `_system/` category templates when no project is
bound to the current session.

When rendering with no bound project:
- `project.*` variables SHALL be empty/absent (existing behaviour — must remain stable)
- `flags` SHALL contain global (feature) flags only, with no project flags merged in
- `feature_flags` SHALL contain global flags (unchanged from bound behaviour)
- `agent.*` variables SHALL be populated from the MCP bootstrap agent info if available,
  or absent if not yet received
- `client.*` variables SHALL be populated from TaskManager cached data if available,
  or absent if not yet received
- `server.*`, formatting variables, `tool_prefix`, `@`, and transient timestamp
  variables SHALL always be available

The rendering pipeline SHALL NOT raise an exception when called with an unbound session.
Any missing project variable SHALL silently default to its empty value, consistent with
how `_build_project_context()` already behaves.

#### Scenario: Render _system template with unbound session
- **WHEN** `render_content(pattern, "_system", extra_context)` is called
- **AND** no project is bound to the current session
- **THEN** the template renders without raising an exception
- **AND** `project.*` variables in the rendered output are empty or absent
- **AND** `feature_flags` contains global flags
- **AND** `agent.*` and `client.*` variables are present if bootstrap data is available

#### Scenario: Render _system template with bound session is unchanged
- **WHEN** `render_content(pattern, "_system", extra_context)` is called
- **AND** a project is bound to the current session
- **THEN** the template renders identically to existing behaviour
- **AND** all project, flag, workflow and client_working_dir variables are populated
  as before

#### Scenario: Missing project variable does not raise
- **WHEN** a `_system/` template references `{{project.name}}` with no bound project
- **THEN** the mustache renderer produces an empty string for that variable
- **AND** no exception is raised
