## ADDED Requirements
### Requirement: Roots Change Handling
The system SHALL handle MCP `roots/list_changed` notifications to detect project switches.

#### Scenario: IDE switches project
- **WHEN** the MCP client sends a `roots/list_changed` notification
- **AND** the new roots resolve to a different project name
- **THEN** the active session calls `switch_project` with the new project name
- **AND** `session.roots` is updated with the new roots list
- **AND** template context cache is invalidated

#### Scenario: Roots change but project unchanged
- **WHEN** the MCP client sends a `roots/list_changed` notification
- **AND** the new roots resolve to the same project name
- **THEN** `session.roots` is updated
- **AND** no project switch occurs

#### Scenario: No active session
- **WHEN** a `roots/list_changed` notification arrives before any session exists
- **THEN** the bootstrap roots ContextVar is updated
- **AND** the next session creation uses the updated roots
