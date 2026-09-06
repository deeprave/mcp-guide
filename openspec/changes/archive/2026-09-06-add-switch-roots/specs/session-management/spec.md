## RENAMED Requirements

- FROM: `### Requirement: Explicit Immutable Root Binding`
- TO: `### Requirement: Explicit Root Binding and Switching`

## MODIFIED Requirements

### Requirement: Session Non-Singleton

The system SHALL implement Session as a non-singleton class with at most one
current bound instance per validated client interaction owner. Different owners
SHALL NOT share a Session. A project switch SHALL replace that owner's bound
instance rather than change its existing instance's project/root identity.

Each Session SHALL own separate listeners, task state, instruction queues and
caches. These mutable resources SHALL NOT be copied or shared when an instance
is replaced. The outgoing instance SHALL be allowed to remain expiring while
its existing work completes.

A Session SHALL be allowed to exist before its project is bound. Its project
SHALL be absent rather than a placeholder. Unbound rendering SHALL still have
access to available agent/client information and global flags.

#### Scenario: Session creation before project binding
- **WHEN** a Session is created before project context is available
- **THEN** it SHALL have no bound Project and SHALL NOT load or persist a placeholder
- **AND** it SHALL NOT depend on ambient ContextVar ownership

#### Scenario: Unbound session rejects bound-only operations
- **GIVEN** a Session has no project binding
- **WHEN** an operation requires persisted project configuration
- **THEN** the defined no-project behaviour SHALL apply
- **AND** the operation SHALL NOT invent or persist project data

#### Scenario: Unbound placeholder rejects bound-only operations
- **GIVEN** no project has been bound
- **WHEN** a project-dependent operation is requested
- **THEN** there SHALL be no placeholder project to save
- **AND** the operation SHALL report the defined no-project condition

#### Scenario: Session creation with immediate project context
- **WHEN** an initial bind operation successfully resolves a project
- **THEN** its Session SHALL become the current bound instance for that owner
- **AND** later requests SHALL use that instance until replacement or expiry

#### Scenario: Unbound session exposes agent and client info for template rendering
- **GIVEN** an unbound Session has received agent/client bootstrap information
- **WHEN** a system template is rendered
- **THEN** the available agent information, client information and global flags SHALL be accessible
- **AND** rendering SHALL NOT require a placeholder or persisted Project

#### Scenario: Replacement owns fresh mutable state
- **GIVEN** an owner's current Session has caches, subscriptions and queued instructions
- **WHEN** a different project selection succeeds
- **THEN** the new bound Session SHALL own fresh mutable state
- **AND** the outgoing Session's mutable resources SHALL NOT become the replacement's resources

### Requirement: Session Lifecycle Management

The system SHALL separate durable project configuration from ephemeral
interaction state. Session instances SHALL follow the lifecycle
`unbound -> bound -> expiring`, followed by disposal. An unbound instance that
never binds SHALL be disposed of when its request work completes.

Unbound request work SHALL be ephemeral. A bound instance SHALL be retained
under its validated public interaction ID only after successful project binding.
A switch SHALL publish a fresh bound instance under that same ID and move the
outgoing instance to expiring. An expiring instance SHALL never become current
again.

Modern interactions SHALL use a validated explicit FastMCP `session_id`.
Retained legacy connections that omit the argument SHALL continue using public
connection identity as their compatibility owner. Modern unbound requests
SHALL NOT gain cross-request state through that fallback.

There SHALL be at most one expiring instance per public ID. A switch received
while that ID has an expiring instance SHALL fail without replacing, queueing
or modifying either existing instance.

Every admitted request and listener/task execution SHALL retain its original
Session instance through completion. Existing work in an expiring Session SHALL
be permitted to finish, including configuration writes to its original project.
New requests and client replies SHALL resolve the current bound Session only.
Expiring instances SHALL receive no new project scheduling or configuration
notifications. Their owned resources SHALL be disposed of after admitted work
finishes, and their expiring entry SHALL then be removed.

Guide interaction state SHALL remain in memory and SHALL NOT be restored after
a server restart. Global configuration storage and its locking remain shared.

#### Scenario: Session persists from unbound to bound state
- **GIVEN** an ephemeral Session has no project
- **WHEN** its initial binding succeeds
- **THEN** that instance SHALL be promoted to the current bound Session
- **AND** its owned bootstrap state SHALL remain attached
- **AND** project-specific runtime work SHALL initialise for the bound project

#### Scenario: Unbound state suppresses project events
- **GIVEN** a Session has no project binding
- **WHEN** an unbound request is handled
- **THEN** project-load and project-switch events SHALL NOT run
- **AND** its first successful bind SHALL use normal initial-bound activation

#### Scenario: Modern request resumes a live interaction
- **GIVEN** the server is running and an interaction has a current bound Session
- **WHEN** a request supplies its valid public session ID
- **THEN** it SHALL resolve the current bound instance without requiring the original connection object
- **AND** it SHALL observe that instance's root and configuration

#### Scenario: Request has no project context
- **WHEN** an interaction has neither a valid root binding nor a successful initial bind
- **THEN** no project configuration SHALL be persisted merely to handle the request
- **AND** project-dependent operations SHALL use the defined no-project behaviour

#### Scenario: Unbound request completes
- **GIVEN** a request and its nested work use an unbound Session
- **WHEN** that work finishes without binding
- **THEN** the ephemeral instance SHALL be cleaned up
- **AND** it SHALL NOT be retained for a later request under the same owner ID

#### Scenario: Expiry does not interrupt an active request
- **GIVEN** a current bound Session has an in-flight request
- **WHEN** idle expiry is evaluated
- **THEN** idle expiry SHALL NOT dispose of that instance
- **AND** its last-used time SHALL reflect completion of its own final request

#### Scenario: Old request completes after replacement
- **GIVEN** a request began on an instance now expiring
- **WHEN** it completes after a replacement is current
- **THEN** completion SHALL release the old instance's request ownership only
- **AND** it SHALL NOT republish the old instance or change the replacement's request accounting

#### Scenario: Existing work saves its original project
- **GIVEN** an admitted operation belongs to an expiring Session
- **WHEN** it saves its original project's configuration
- **THEN** the save SHALL remain permitted through normal shared configuration locking
- **AND** it SHALL NOT be redirected to the replacement's project or rejected solely because the Session is expiring
- **AND** normal publication SHALL still reach active users of the saved configuration

#### Scenario: Follow-up client reply after a switch
- **GIVEN** a project switch has published a replacement under the same public ID
- **WHEN** the client submits another request, including a file or command reply
- **THEN** that request SHALL use the current bound Session and project
- **AND** the system SHALL NOT route it to an expiring Session or require a historical binding token

#### Scenario: Another switch while the ID is expiring
- **GIVEN** the public ID already has an expiring Session
- **WHEN** any further switch is requested for that ID
- **THEN** the switch request SHALL fail explicitly before changing either instance
- **AND** it SHALL NOT create another expiring instance or enqueue a switch
- **AND** the existing bound and expiring Sessions SHALL remain unchanged

#### Scenario: Expiring work finishes
- **GIVEN** an expiring Session has stopped admitting new work
- **WHEN** all its admitted work has completed
- **THEN** its listeners, tasks, timers, queues and caches SHALL be disposed of
- **AND** its expiring entry SHALL be removed
- **AND** a later valid switch for that public ID SHALL be permitted

#### Scenario: Cleanup is incomplete
- **GIVEN** disposal of an expiring Session fails
- **WHEN** cleanup reports that failure
- **THEN** it SHALL NOT silently restore the old instance as current
- **AND** the system SHALL NOT silently admit another expiring instance under that ID

#### Scenario: Outgoing cleanup does not control the switch response
- **GIVEN** a switch has successfully published its replacement
- **WHEN** the outgoing instance becomes eligible for disposal
- **THEN** runtime SHALL own and track disposal independently of request completion
- **AND** cleanup latency or failure SHALL NOT replace the successful switch response
- **AND** a failed disposal SHALL remain registered and be reported separately

#### Scenario: Idle disposal retains ownership
- **WHEN** idle expiry selects a bound instance
- **THEN** it SHALL use the same expiring lifecycle and retain failed disposal
- **AND** it SHALL skip an owner that already has an expiring instance
- **AND** a pending idle disposal SHALL prevent a new initial binding for that owner

#### Scenario: One Session cleanup fails during runtime shutdown
- **GIVEN** runtime owns unbound, bound or expiring Sessions
- **WHEN** one Session's cleanup raises during shutdown
- **THEN** cleanup SHALL still be attempted for every remaining instance
- **AND** runtime registries and shared services SHALL be shut down before reporting the failure

#### Scenario: Concurrent contexts are isolated
- **GIVEN** requests belong to different interaction owners or concrete Session instances
- **WHEN** their work overlaps
- **THEN** their listeners, transient state and project bindings SHALL remain instance-owned
- **AND** completing one request SHALL NOT replace another's active context

#### Scenario: Subagent uses the same root
- **WHEN** a subagent binds its own interaction to the same root as a parent
- **THEN** the interactions SHALL have separate Sessions and task state
- **AND** they SHALL be permitted to use the same durable project configuration
- **AND** their pending instructions, timers and caches SHALL NOT be shared

#### Scenario: Parent and subagent use different session IDs
- **WHEN** a parent and subagent use separate validated IDs
- **THEN** their current and expiring Sessions SHALL remain separate
- **AND** the system SHALL NOT infer shared ownership from names, roots or process ancestry

### Requirement: Explicit Root Binding and Switching

The system SHALL establish an interaction's initial client root through
`set_project(path)` and validated selected-root state. Initial binding SHALL
require an absolute client path and SHALL reject name-only input or a second
initial binding, including an unchanged path.

Each bound Session SHALL retain its root and configuration identity unchanged
for its lifetime. `switch_project(name | path)` SHALL select a fresh current
Session when the requested selection differs: name-only keeps the interaction's
current root; path-only uses the normalised path and its basename. The public
interaction owner and session ID SHALL remain unchanged.

Path normalisation SHALL be lexical and SHALL NOT require client paths to exist
on the server or resolve client filesystem links. Configuration identity SHALL
remain `(name, bound_root_hash)`; both the generated configuration key and stored
hash SHALL match. Name-only, malformed, missing-hash and mismatched-hash stored
entries SHALL be ignored without legacy configuration migration.

#### Scenario: New interaction selects its first root
- **WHEN** an unbound interaction successfully calls set_project with an absolute client path
- **THEN** its initial Session SHALL bind to that root
- **AND** other interactions SHALL remain unchanged

#### Scenario: New interaction selects a different root
- **GIVEN** another interaction already has a root binding
- **WHEN** a new interaction selects a different root
- **THEN** the new interaction SHALL receive its own binding
- **AND** the prior interaction SHALL remain unchanged

#### Scenario: Initial binding requires an absolute path
- **WHEN** an unbound interaction supplies a name, relative path or missing path
- **THEN** the selection SHALL be rejected without binding a project
- **AND** guidance SHALL request an absolute client root through set_project

#### Scenario: Agent supplies a project name rather than a path
- **WHEN** an unbound interaction supplies a project name instead of an initial path
- **THEN** the system SHALL reject the selection without creating a project
- **AND** it SHALL direct the agent to provide the absolute root as path

#### Scenario: Second initial binding is rejected
- **GIVEN** an interaction is already bound
- **WHEN** set_project is called again, including for its current path
- **THEN** it SHALL fail without replacing or rebinding the current Session

#### Scenario: Name-only selection retains the root
- **GIVEN** the interaction is bound and no instance for its ID is expiring
- **WHEN** a different configuration name is selected
- **THEN** a fresh current Session SHALL use that name with the existing root
- **AND** the outgoing instance SHALL retain its original name and root

#### Scenario: Configuration selection does not change root binding
- **GIVEN** a bound interaction selects a different configuration name
- **WHEN** the switch succeeds
- **THEN** the replacement SHALL use the prior root's hash with the supplied name
- **AND** the interaction's root path SHALL remain unchanged

#### Scenario: Path selection replaces the bound Session
- **GIVEN** the interaction is bound and no instance for its ID is expiring
- **WHEN** a different root is selected successfully
- **THEN** the replacement SHALL use the normalised root and its basename configuration
- **AND** the public session ID SHALL remain unchanged
- **AND** the outgoing Session SHALL retain its original binding while expiring

#### Scenario: Same selection without pending expiry
- **GIVEN** no Session for the public ID is expiring
- **WHEN** a valid switch resolves to the current name and root
- **THEN** the operation SHALL succeed without replacement or task restart

#### Scenario: Root changes initialise fresh project state
- **GIVEN** the old and new roots can have the same basename
- **WHEN** the interaction switches roots
- **THEN** the replacement SHALL initialise its own tasks, instructions and caches
- **AND** correctness SHALL NOT depend on clearing or resetting the outgoing Session before reuse

#### Scenario: Same configuration name at different roots
- **WHEN** interactions at different roots select the same name
- **THEN** the resulting configuration identities SHALL have their respective root hashes
- **AND** their configurations SHALL remain independent

#### Scenario: Same name has a different or missing hash
- **WHEN** a stored entry with the requested name has a missing or mismatched root hash
- **THEN** it SHALL NOT be selected by name alone
- **AND** only the correctly keyed configuration SHALL be selected or created

#### Scenario: Background work has no client request
- **WHEN** background work executes without a current client request
- **THEN** it SHALL NOT discover or select client roots
- **AND** it SHALL use only its explicitly owned project state
