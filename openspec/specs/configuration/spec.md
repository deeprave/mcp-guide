# configuration Specification

## Purpose

Define Guide's runtime-owned persisted configuration service, configuration
snapshots, and scoped update publication.

## Requirements

### Requirement: Runtime-owned configuration service

GuideRuntime SHALL own one configuration service for its process. Sessions and
feature-flag handlers SHALL use that runtime-owned service rather than create
independent configuration managers.

#### Scenario: Session reads project configuration

- **WHEN** a Session needs project configuration
- **THEN** it obtains it from its GuideRuntime's configuration service

### Requirement: Safe persisted configuration mutation

The configuration service SHALL persist the YAML configuration under the shared
file-update lock. Concurrent mutations SHALL be serialised, and a failed
operation SHALL not publish a replacement snapshot.

#### Scenario: Configuration write succeeds

- **WHEN** the service updates persisted configuration
- **THEN** it writes the complete updated configuration under the shared lock
- **AND** later readers observe that complete configuration

#### Scenario: Configuration write fails

- **WHEN** a configuration mutation cannot be completed
- **THEN** it reports the failure without publishing a changed configuration
  snapshot

### Requirement: Project configuration persistence

The service SHALL persist and retrieve project configurations by their strict
project identity, including creating, updating, listing, renaming, and deleting
stored projects.

#### Scenario: Project configuration is updated

- **WHEN** a project configuration is updated
- **THEN** the service persists the replacement under that project's identity

### Requirement: Absolute default docroot

When a configuration file lacks a usable `docroot`, the service SHALL persist
an absolute default located beside that configuration file. It SHALL not infer
a current-working-directory-relative docroot or unpack templates into a source
worktree merely to establish the default.

#### Scenario: Configuration has no docroot

- **WHEN** a configuration file has no usable `docroot`
- **THEN** the service stores an absolute default docroot beside the
  configuration file

### Requirement: Configuration snapshot publication

The service SHALL detect persisted configuration changes, validate and compare
the replacement snapshot with its current snapshot, and publish one immutable
delta to GuideRuntime. The service SHALL not select or invoke Sessions itself.

#### Scenario: Persisted configuration changes

- **WHEN** the configuration file changes
- **THEN** the service publishes changed global flags and strict project
  identities to GuideRuntime

#### Scenario: Runtime distributes a scoped update

- **WHEN** a published delta affects multiple live bound Sessions
- **THEN** GuideRuntime independently queues an update for each affected
  Session
- **AND** it does not update unbound or unrelated Sessions

### Requirement: Configuration watcher resilience

The configuration watcher SHALL detect replacement and modification of its
file, retain a single active watcher per runtime configuration service, and
continue monitoring after transient filesystem or callback failures.

#### Scenario: Configuration file is replaced

- **WHEN** the watched configuration file is replaced
- **THEN** the watcher detects the replacement and triggers snapshot refresh

#### Scenario: Watch callback fails

- **WHEN** a configuration watch callback fails
- **THEN** the watcher logs the failure and remains active
