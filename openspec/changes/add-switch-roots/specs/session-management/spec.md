## RENAMED Requirements

- FROM: `### Requirement: Explicit Immutable Root Binding`
- TO: `### Requirement: Explicit Root Binding and Switching`

## MODIFIED Requirements

### Requirement: Explicit Root Binding and Switching
The system SHALL establish an interaction's first client filesystem root through
`set_project(path)` and validated selected-root state. `set_project(path)` SHALL
require an absolute client filesystem path, derive root identity from it, and
reject name-only selection or any second binding for the same interaction.

`switch_project(name?, path?)` SHALL retain the current root for name-only
configuration selection. When it receives `path`, it SHALL atomically replace the
interaction's root and active configuration identity while retaining the same
Guide session owner and session ID. Path normalisation SHALL be lexical and SHALL
not require the target client path to exist or resolve client filesystem links.

Configuration identity SHALL use `(name, bound_root_hash)`. A path-only switch
uses the new root's basename as its configuration name; a switch with both values
uses the supplied name and new root hash. Resolution SHALL require both the
generated `<project-name>-<hash>` key and stored configuration hash to match the
selected root hash. Name-only, malformed, missing-hash, and mismatched-hash
entries SHALL be ignored. The system SHALL provide no legacy configuration
migration; it SHALL select or create only the correct key for the selected root.

#### Scenario: New interaction selects its first root
- **WHEN** an agent begins a new interaction and explicitly calls `set_project`
  with an absolute root path
- **THEN** the system SHALL bind the interaction to that root
- **AND** it SHALL leave every other interaction's root state unchanged

#### Scenario: New interaction selects a different root
- **WHEN** an agent begins a new interaction and explicitly selects a different root path
- **THEN** the system SHALL bind the new interaction to that root
- **AND** it SHALL leave the prior interaction's root state unchanged

#### Scenario: Initial binding requires an absolute path
- **WHEN** an unbound interaction calls `set_project` with a name, relative path,
  or no path
- **THEN** the system SHALL reject the selection without creating or binding a project
- **AND** it SHALL direct the agent to provide an absolute client filesystem root

#### Scenario: Agent supplies a project name rather than a path
- **WHEN** an unbound interaction calls project selection with a name, relative path, or no path
- **THEN** the system SHALL reject the selection without creating or binding a project
- **AND** it SHALL direct the agent to provide the absolute client filesystem root as `path`

#### Scenario: Second initial binding is rejected
- **WHEN** a root-bound interaction calls `set_project`, including with its current path
- **THEN** the system SHALL reject the request
- **AND** it SHALL retain the existing root and active configuration identity

#### Scenario: Name-only selection retains the root
- **WHEN** a root-bound interaction calls `switch_project` with only a configuration name
- **THEN** the system SHALL retain the interaction's bound root path unchanged
- **AND** it SHALL resolve the configuration using that root's hash and supplied name

#### Scenario: Configuration selection does not change root binding
- **WHEN** a root-bound interaction calls `switch_project` with a configuration name
- **THEN** the system SHALL change the active configuration selection if valid
- **AND** it SHALL retain the interaction's bound root path unchanged
- **AND** it SHALL resolve the configuration using that root's hash and the supplied name

#### Scenario: Path selection changes the root in the same session
- **WHEN** a root-bound interaction calls `switch_project` with a valid path
- **THEN** the system SHALL retain its Guide session ID and interaction ownership
- **AND** it SHALL replace both root binding and active configuration identity
- **AND** later requests using that session ID SHALL receive the new root and configuration

#### Scenario: Root changes refresh project-scoped state
- **WHEN** a root switch succeeds, including where the prior and new configuration names match
- **THEN** the system SHALL notify project-change listeners
- **AND** it SHALL invalidate or replace project-scoped tasks, instructions, cached flags,
  and template context for the new root

#### Scenario: Same configuration name at different roots
- **WHEN** interactions bound to different root paths each select the same configuration name
- **THEN** the system SHALL resolve configuration identities with different root hashes
- **AND** the configurations SHALL remain independent

#### Scenario: Same name has a different or missing hash
- **WHEN** an interaction selects a configuration name for which stored entries have a different or missing hash
- **THEN** the system SHALL NOT select any of those entries by name
- **AND** it SHALL ignore those entries and resolve or create only the correctly keyed
  configuration for the selected root hash

#### Scenario: Background work has no client request
- **WHEN** background work runs without a current request context
- **THEN** it SHALL NOT issue a server-to-client roots request or use root data
- **AND** it SHALL only operate on explicitly owned project state
