## MODIFIED Requirements

### Requirement: Session Non-Singleton
The system SHALL implement Session as a non-singleton class. One Session exists per
client connection. In HTTP transport, each concurrent client has its own Session via
ContextVar task isolation.

Session SHALL own per-client caches including command discovery cache, ensuring no
cross-client cache contamination.

#### Scenario: Session creation
- **WHEN** `get_session()` is called and no session exists in the current async context
- **THEN** a new Session is created with auto-resolved project name
- **AND** the session is stored in the ContextVar
- **AND** subsequent `get_session()` calls return the same instance

#### Scenario: Concurrent HTTP clients isolated
- **WHEN** multiple clients connect via HTTP transport
- **THEN** each client has its own Session instance via ContextVar task isolation
- **AND** session state for one client does not affect another
- **AND** command cache, file cache, and task manager are isolated per-client

## ADDED Requirements

### Requirement: Per-Task File Cache
The system SHALL maintain file cache state per async task using a ContextVar, not as a
module-level singleton.

Each client connection SHALL have its own `FileCache` instance. File content sent by
one agent SHALL NOT be visible to another.

#### Scenario: File cache isolation
- **WHEN** Client A sends file content via `send_file_content`
- **THEN** the content is cached in Client A's task-local FileCache
- **AND** Client B's FileCache does not contain Client A's files

### Requirement: Per-Task Task Manager
The system SHALL maintain a TaskManager instance per async task using a ContextVar, not
as a class-level singleton.

Each client connection SHALL have its own TaskManager with isolated instruction queue,
timer tasks, and event dispatch.

#### Scenario: Task manager isolation
- **WHEN** Client A queues an instruction via the task manager
- **THEN** only Client A receives that instruction
- **AND** Client B's task manager is unaffected

#### Scenario: On-demand creation
- **WHEN** `get_task_manager()` is called and no manager exists in the current task
- **THEN** a new TaskManager is created and stored in the ContextVar
