## MODIFIED Requirements

### Requirement: Enabled values select a handoff target
When the effective `handoff-context` value is `true`, the system SHALL request
updates to `context/<workspace-context-name>.json` under the shared configured documents directory. The context name SHALL be resolved independently of issue selection and SHALL survive session replacement and worktree removal. When it is a filename,
the system SHALL request updates to that filename under `{{paths.documents}}`.
When it is a relative file path, the system SHALL request updates to that
resolved project path. An absolute path SHALL be rejected.

#### Scenario: Boolean enablement uses the default target
- **WHEN** `handoff-context` is true
- **THEN** startup guidance SHALL identify the exact shared `context/<workspace-context-name>.json` target
- **AND** the main checkout SHALL use `context/root.json`
- **AND** it SHALL request an updated and current handoff context

#### Scenario: Filename selects a document-directory target
- **WHEN** `handoff-context` contains a filename without directory components
- **THEN** startup guidance SHALL identify that filename beneath `{{paths.documents}}`
- **AND** it SHALL request an updated and current handoff context

#### Scenario: Relative path selects an explicit target
- **WHEN** `handoff-context` contains a relative path with directory components
- **THEN** startup guidance SHALL identify the resolved relative target
- **AND** it SHALL not relocate that target beneath `{{paths.documents}}`

#### Scenario: Absolute path is rejected
- **WHEN** a caller sets `handoff-context` to an absolute path
- **THEN** feature-flag validation SHALL reject the value

#### Scenario: Legacy default is preserved during migration

- **GIVEN** the former default `context.json` exists in the documents directory
- **WHEN** named workspace contexts are introduced
- **THEN** Guide SHALL preserve the legacy file and identify it during transition
- **AND** migration to `context/root.json` SHALL require an explicit choice and SHALL NOT overwrite an existing target


## ADDED Requirements

### Requirement: Locked root handover updates

All Guide-managed updates to the shared root handover SHALL use a common cross-process lock and atomic read-modify-write operation on the filesystem holding that handover. Root-agent updates SHALL preserve consolidated workspace entries. Guide guidance SHALL direct agents through the coordinated write operation. Failure to obtain a safe lock SHALL leave existing handover files unchanged and produce a retryable diagnostic.

#### Scenario: Concurrent retirement and root update

- **GIVEN** a root agent and two retiring workspaces update root.json concurrently
- **WHEN** their updates complete
- **THEN** root.json SHALL contain the root update and both workspace entries without lost updates
- **AND** every writer SHALL participate in the same locking protocol

### Requirement: Consolidation on explicit workspace retirement

Explicit worktree retirement SHALL preserve its final handover as a named entry in root.json before removing the original context file. It SHALL preserve other root content, serialise against source updates and support idempotent retries. The registry SHALL retain the durable context name and consolidated location. Agent shutdown, disconnection or replacement alone SHALL NOT trigger consolidation or deletion. Unexpected checkout disappearance SHALL retain detached context pending explicit retirement or resume.

#### Scenario: Successful retirement

- **GIVEN** a workspace has a final context payload
- **WHEN** that workspace is explicitly retired
- **THEN** its payload SHALL be durably preserved under its context name in root.json
- **AND** only after that commit SHALL its original context file be removed
- **AND** central lookup SHALL identify its consolidated location

#### Scenario: Agent stops without retirement

- **GIVEN** a workspace has handover context
- **WHEN** its agent stops or is replaced without explicit worktree retirement
- **THEN** its separate context SHALL remain available for resumption
- **AND** it SHALL NOT be consolidated or deleted solely because the agent stopped

#### Scenario: Consolidation fails or cleanup is interrupted

- **GIVEN** retirement is in progress
- **WHEN** root persistence fails or execution stops before source cleanup
- **THEN** the original context SHALL remain until its payload is durably preserved
- **AND** retry SHALL complete without duplicate consolidation or deleting a newer source revision
