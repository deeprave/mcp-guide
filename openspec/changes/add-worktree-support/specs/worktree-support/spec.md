## Purpose

Support independent worktree workflow state for concurrent agents while sharing
repository configuration and documents across linked Git worktrees.

## ADDED Requirements

### Requirement: Distinct repository and worktree binding

Guide SHALL retain a session-owned absolute client `worktree` path separately
from the project identity root. Initial binding SHALL accept an optional
worktree path defaulting to the project root.

#### Scenario: Initial worktree default
- **WHEN** initial binding omits worktree
- **THEN** worktree equals project root

### Requirement: Allocated worktree name

Guide SHALL allocate a readable worktree name for a new linked-worktree handoff. The name and worktree path SHALL be recorded in shared handover context. Clients SHALL NOT choose the name for a new worktree; a child receives the allocated label from its handoff. An existing linked worktree's local workflow file is authoritative for its label. The label SHALL NOT affect project configuration identity.

#### Scenario: Linked worktree receives a generated name
- **GIVEN** a parent requests a new linked-worktree handoff
- **WHEN** Guide allocates the handoff
- **THEN** Guide assigns a readable worktree name
- **AND** instructs the parent to record the name and path in shared handover context

#### Scenario: Child receives its worktree name
- **GIVEN** a shared handover entry contains a linked-worktree name and path
- **WHEN** a parent spawns the assigned child
- **THEN** the child receives the allocated name
- **AND** resolves its intended path and task from the handover entry

### Requirement: Handoff context remains client-owned

Guide SHALL direct agents to update the configured handoff context but SHALL NOT request, receive, cache, or use its content as workflow state.

#### Scenario: Guide does not consume handoff content
- **WHEN** an agent updates handoff context
- **THEN** Guide SHALL retain no copy of that content
- **AND** SHALL derive workflow state from the worktree workflow file

### Requirement: Shared handover context is worktree-keyed

Worktree-specific handover data SHALL be stored at `worktrees.<name>` in the shared context object. Reserved top-level sections MAY contain global todo notes or ancillary information and SHALL be preserved. The primary checkout SHOULD use `worktrees.root`.

#### Scenario: Concurrent worktree handovers
- **GIVEN** two linked-worktree sessions update shared handover context
- **WHEN** each writes its `worktrees.<name>` entry
- **THEN** each worktree entry is preserved
- **AND** neither update replaces the other worktree entry

#### Scenario: Root handover preserves global information
- **GIVEN** shared context contains reserved global sections
- **WHEN** the primary checkout updates its `worktrees.root` handover entry
- **THEN** Guide SHALL preserve the global sections
- **AND** SHALL not replace another worktree entry

### Requirement: Client context updates are locked and atomic

The client SHALL create an adjacent context lock, reread and validate the document, merge only the caller entry, atomically replace the document, and remove the lock.

#### Scenario: Client updates one worktree entry
- **GIVEN** a client holds the context lock for its worktree
- **WHEN** it updates handover context
- **THEN** it SHALL preserve other worktree entries
- **AND** SHALL atomically replace the context document before releasing its lock

### Requirement: Context locks use modification time

A context lock SHALL identify the holding worktree. Its modification time SHALL be the sole activity signal. A lock older than one minute is inactive and may be replaced.

#### Scenario: Client replaces an inactive lock
- **GIVEN** an adjacent context lock is older than one minute
- **WHEN** a client needs to update context
- **THEN** it SHALL replace the inactive lock

### Requirement: Handoff-context gates worktree commands

Guide SHALL make worktree commands available when `handoff-context` is absent or enabled, its resolved target is eligible JSON or YAML, and `workflow-file` is a basename. An explicit `handoff-context: false`, an ineligible or non-structured handoff target, or an absolute or directory-qualified workflow-file SHALL disable them with migration or configuration guidance. Guide SHALL NOT introduce a separate worktree feature or project flag.

#### Scenario: Handoff context is explicitly disabled
- **GIVEN** `handoff-context` is explicitly `false`
- **WHEN** an agent requests a worktree command
- **THEN** Guide SHALL explain that worktree support requires handoff context
- **AND** SHALL not create, register, or bind a worktree through that command

#### Scenario: Handoff context is absent
- **GIVEN** no project or global `handoff-context` value is set
- **WHEN** an agent requests a worktree command
- **THEN** Guide SHALL resolve the default shared handoff target
- **AND** SHALL make the command available when that target is eligible

### Requirement: New worktree branch selection

When `guide://_worktree/new` receives no branch, Guide SHALL elicit branch selection. An existing selected branch SHALL be checked out; a new branch SHALL be created from `main`, not from the primary checkout's current branch.

#### Scenario: Parent selects a new branch
- **GIVEN** a parent requests a new worktree without a branch
- **WHEN** the parent supplies a branch that does not exist
- **THEN** Guide SHALL instruct it to create that branch from `main`

### Requirement: New worktree path

Guide SHALL instruct a new linked worktree to use a sibling path named `{{project-name}}_{{worktree-name}}`, where the project name is the primary checkout directory name and the worktree name is the allocated label.

#### Scenario: Guide allocates a sibling worktree path
- **GIVEN** the primary checkout is `/Users/davidn/Code/mcp-guide`
- **AND** Guide allocates worktree name `ludicrous-naming`
- **WHEN** a parent requests a new linked worktree
- **THEN** Guide SHALL instruct it to create `/Users/davidn/Code/mcp-guide_ludicrous-naming`

### Requirement: Fresh worktree session preflight

Before worktree operations, a spawned agent SHALL report its current directory through the client working-directory signal. If the reported worktree differs from the session binding, Guide SHALL preserve the existing session unchanged and return instructions to establish a fresh interaction using `set_project` with the project root and current worktree. Spawn guidance SHALL NOT forward the parent session identifier.

#### Scenario: Spawned agent reports a different worktree
- **GIVEN** a session is bound to worktree A
- **WHEN** an agent reports a current directory in linked worktree B
- **THEN** Guide SHALL not rebind the existing session
- **AND** SHALL instruct the agent to create a fresh session bound to project root A and worktree B

### Requirement: Worktree configuration identity

Linked worktrees SHALL share the repository-root configuration key and hash;
worktree paths, branches, and remotes SHALL NOT change it. Independent clones
SHALL remain independent projects. Existing root-authorisation and client-path
normalisation rules apply.

#### Scenario: Two worktrees share configuration

- **GIVEN** two independent sessions bind the same repository root and different linked checkout roots
- **WHEN** a shared configuration update is published
- **THEN** both sessions SHALL observe it
- **AND** each SHALL preserve its own worktree and workflow state

#### Scenario: Existing caller omits worktree

- **GIVEN** a caller supplies only the project root
- **WHEN** initial binding succeeds
- **THEN** worktree SHALL equal the project root
- **AND** configuration identity SHALL remain unchanged

#### Scenario: Repository has no remote

- **GIVEN** a Git repository has linked worktrees and no configured remote
- **WHEN** the client discovers repository and checkout roots
- **THEN** Guide SHALL support shared configuration binding without requiring a remote URL

#### Scenario: Remote client filesystem

- **GIVEN** client filesystem sharing is not verified
- **WHEN** binding or checkout discovery requires filesystem information
- **THEN** Guide SHALL request client-provided information
- **AND** SHALL NOT resolve those paths using the server's unrelated filesystem

### Requirement: Client worktree discovery

Guide SHALL provide `guide://_worktree/list` to request a client Git worktree inventory. The agent SHALL send the inventory through `send_file_content` with path `.git-worktrees.json`. Guide SHALL treat the report as client-provided discovery data and SHALL NOT require a remote URL or create the report as a project file. Guide SHALL cache the report for one minute in the bound session; worktree commands SHALL require a current report and request refresh when it is absent, expired, or known stale after a worktree change.

#### Scenario: Client reports linked worktrees
- **GIVEN** Guide cannot inspect the client filesystem directly
- **WHEN** an agent requests `guide://_worktree/list`
- **THEN** Guide SHALL instruct the agent to send the current Git worktree inventory as `.git-worktrees.json`
- **AND** SHALL use the received report for subsequent worktree guidance

#### Scenario: Cached inventory expires
- **GIVEN** Guide received a client worktree inventory more than one minute ago
- **WHEN** an agent requests a worktree command that needs inventory
- **THEN** Guide SHALL request a new inventory before continuing

### Requirement: Scoped worktree path resolution

Guide SHALL resolve a basename-only workflow-file setting against the session
worktree. Absolute or directory-qualified workflow-file settings SHALL disable
worktree support.

#### Scenario: Worktree-relative workflow path
- **WHEN** a session resolves its default workflow file
- **THEN** it uses its worktree

### Requirement: Worktree-labelled workflow state

Each linked-worktree workflow file SHALL include a `worktree` field containing the worktree name. When a linked-worktree session first receives a valid workflow file, Guide SHALL adopt that label for the session. If the existing file lacks a label, the agent SHALL add the allocated session label before submitting it. Later workflow files SHALL match the adopted label. For the primary checkout, an omitted `worktree` field SHALL default to `root`; a linked worktree SHALL initialise a new workflow file from its shared handover entry.

#### Scenario: Agent reads its linked-worktree workflow file
- **GIVEN** a session is bound to a linked worktree named `languid_lizard`
- **WHEN** Guide receives that worktree's workflow file
- **THEN** it SHALL adopt and accept the file when `worktree` is `languid_lizard`
- **AND** SHALL reject a file labelled for a different worktree

### Requirement: Worktree path visibility and authorisation

Binding a worktree SHALL NOT grant unrestricted access outside authorised
project/worktree paths. Absolute workflow overrides remain explicit and shared
target conflicts diagnosable.

#### Scenario: Independent workflow files and shared scratch space

- **GIVEN** two sessions use different worktrees for one project
- **WHEN** default paths are resolved
- **THEN** each SHALL use its own worktree `.guide.yaml`
- **AND** an absent local workflow file SHALL NOT cause fallback to the other worktree's file

#### Scenario: Workflow events cannot cross sessions

- **GIVEN** two worktree workflow files have the same basename
- **WHEN** one session reports or observes a workflow update
- **THEN** only its owning worktree workflow cache SHALL change
- **AND** routing SHALL use the bound session and matching workflow basename

#### Scenario: Commands operate on the active checkout

- **GIVEN** a session is bound to a linked worktree
- **WHEN** Guide provides repository review, build or branch/reset instructions
- **THEN** those instructions SHALL target that worktree rather than the main checkout

### Requirement: Project-wide worktree visibility

Guide SHALL expose richer observed worktree information through
`guide://_worktree/list?verbose`, using client Git checkout discovery where
necessary. Active reported checkout paths SHALL become permitted read roots for
the project. Workflow state SHALL come from a readable worktree workflow file,
not client handoff metadata. Inaccessible or unobserved paths SHALL NOT be
presented as confirmed removed.

#### Scenario: Observe concurrent work

- **GIVEN** multiple checkouts belong to the bound repository
- **WHEN** verbose worktree listing is requested
- **THEN** each observed checkout SHALL have separately attributed workflow state
- **AND** last-observed or unavailable information SHALL be labelled accurately

### Requirement: Fresh Guide binding for spawned worktree agents

An agent assigned to a separate worktree SHALL establish a fresh Guide interaction/session and explicitly bind the shared project root and assigned worktree before worktree operations. Guide-provided spawning guidance SHALL NOT direct the new agent to reuse the parent session ID. A bound session identifier SHALL NOT be accepted to change that interaction's worktree; rejection SHALL preserve its original state. Existing configuration propagation SHALL NOT replace the worktree binding.

#### Scenario: Spawned agent binds its own checkout

- **GIVEN** a parent agent is bound to the main checkout and creates a linked worktree
- **WHEN** a new agent begins work in that checkout
- **THEN** it SHALL establish a distinct Guide session bound to that worktree and the shared project identity
- **AND** the parent session SHALL remain bound to its original worktree

#### Scenario: Reused session attempts worktree reassignment

- **GIVEN** a session is already bound to worktree A
- **WHEN** a request supplies that session identifier to bind worktree B
- **THEN** Guide SHALL reject the reassignment and request a fresh interaction
- **AND** worktree A's binding and workflow cache SHALL remain unchanged
