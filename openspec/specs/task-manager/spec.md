## ADDED Requirements

### Requirement: Deferred Project-Bound Initialization
The task manager SHALL support startup before a real project is available.

Project-independent startup work MAY run during server initialization, but
project-sensitive initialization SHALL be deferred until the session is bound to a
real project.

#### Scenario: Server startup without MCP context
- **WHEN** the server runs startup hooks before any client request context exists
- **THEN** task manager initialization SHALL complete without requiring immediate project resolution
- **AND** no failure SHALL occur solely because client roots are not yet available

#### Scenario: First project-bound initialization
- **WHEN** the session later binds to a real project
- **THEN** the task manager SHALL initialize resolved flags and other project-sensitive state at that time
- **AND** deferred initialization SHALL run at most once per project bind event
