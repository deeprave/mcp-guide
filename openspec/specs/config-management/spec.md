# config-management Specification

## Purpose
Define configuration loading, change detection, snapshots, and runtime publication.
## Requirements
### Requirement: Config File Change Detection
The system SHALL automatically detect configuration file modifications,
compare the validated current snapshot with the previous snapshot, and publish
one immutable configuration snapshot delta to the process runtime. ConfigManager
SHALL NOT register, select, or invoke Session instances.

#### Scenario: Config file modified
- **WHEN** a configuration file is modified on disk
- **THEN** the system validates and diffs the replacement snapshot against the
  cached snapshot
- **AND** publishes the old/new snapshots, global-flag change information, and
  changed strict project identities to the process runtime

#### Scenario: Multiple sessions active
- **WHEN** multiple sessions are active and a configuration file change affects
  more than one of their effective configurations
- **THEN** the process runtime selects each affected live bound session and
  delivers an independent scoped update
- **AND** unbound, expiring, and sessions for unrelated project identities
  receive no update
- **AND** failure reconciling one session does not affect others

### Requirement: File Content Caching
The system SHALL cache configuration file content and invalidate cache on file changes.

#### Scenario: Cache hit on unchanged file
- **WHEN** configuration content is requested and file is unchanged
- **THEN** cached content is returned without file system access

#### Scenario: Cache invalidation on change
- **WHEN** configuration file is modified
- **THEN** cached content is invalidated
- **AND** next access reads fresh content from disk

### Requirement: Cross-Platform File Monitoring
The system SHALL reliably detect file changes across different operating systems and file systems.

#### Scenario: File modification detection
- **WHEN** file modification time (mtime) changes
- **THEN** change is detected and callbacks are invoked

#### Scenario: File replacement detection
- **WHEN** file inode changes (file replaced)
- **THEN** change is detected and callbacks are invoked

### Requirement: Watcher Instance Management
The system SHALL prevent duplicate watchers for the same file path and manage watcher lifecycle.

#### Scenario: Duplicate watcher prevention
- **WHEN** attempting to create a second watcher for the same path
- **THEN** an error is raised indicating watcher already exists

#### Scenario: Automatic cleanup
- **WHEN** watcher is stopped or goes out of scope
- **THEN** it is automatically removed from the registry

### Requirement: Error Resilience
The system SHALL handle file system errors gracefully without crashing the watcher.

#### Scenario: File access error
- **WHEN** file becomes temporarily inaccessible
- **THEN** watcher continues monitoring and logs the error
- **AND** normal operation resumes when file becomes accessible

#### Scenario: Callback exception isolation
- **WHEN** a registered callback raises an exception
- **THEN** other callbacks continue to be invoked
- **AND** the watcher remains operational
