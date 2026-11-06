## Purpose

Support independent workspace workflow state for concurrent agents while sharing
repository configuration and documents across linked Git worktrees.

## ADDED Requirements

### Requirement: Distinct repository and workspace binding

Guide SHALL retain a session-owned absolute client `workspace_root` separately
from the project identity root. Initial binding SHALL accept an optional
workspace root defaulting to the project root.

#### Scenario: Initial workspace default
- **WHEN** initial binding omits workspace root
- **THEN** workspace_root equals project root

### Requirement: Worktree configuration identity

Linked worktrees SHALL share the repository-root configuration key and hash;
workspace paths, branches, and remotes SHALL NOT change it. Independent clones
SHALL remain independent projects. Existing root-authorisation and client-path
normalisation rules apply.

#### Scenario: Two workspaces share configuration

- **GIVEN** two independent sessions bind the same repository root and different linked checkout roots
- **WHEN** a shared configuration update is published
- **THEN** both sessions SHALL observe it
- **AND** each SHALL preserve its own workspace root and workflow state

#### Scenario: Existing caller omits workspace

- **GIVEN** a caller supplies only the project root
- **WHEN** initial binding succeeds
- **THEN** workspace_root SHALL equal the project root
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

### Requirement: Scoped workspace path resolution

Guide SHALL resolve relative workflow-file settings against the session
workspace root.

#### Scenario: Workspace-relative workflow path
- **WHEN** a session resolves its default workflow file
- **THEN** it uses its workspace root

### Requirement: Workspace path visibility and authorisation

Binding a workspace SHALL NOT grant unrestricted access outside authorised
project/workspace paths. Absolute workflow overrides remain explicit and shared
target conflicts diagnosable.

#### Scenario: Independent workflow files and shared scratch space

- **GIVEN** two sessions use different workspaces for one project
- **WHEN** default paths are resolved
- **THEN** each SHALL use its own workspace `.guide.yaml`
- **AND** an absent local workflow file SHALL NOT cause fallback to the other workspace's file

#### Scenario: Workflow events cannot cross sessions

- **GIVEN** two workspace workflow files have the same basename
- **WHEN** one session reports or observes a workflow update
- **THEN** only its owning workspace workflow cache SHALL change
- **AND** routing SHALL distinguish full resolved paths

#### Scenario: Commands operate on the active checkout

- **GIVEN** a session is bound to a linked worktree
- **WHEN** Guide provides repository review, build or branch/reset instructions
- **THEN** those instructions SHALL target that workspace rather than the main checkout

### Requirement: Project-wide workspace visibility

Guide SHALL offer a workspace overview through `guide://_workspaces`, using
client Git checkout discovery where necessary. It SHALL identify workspace
paths, available branch/workflow state, and observation timestamps. Inaccessible
or unobserved paths SHALL NOT be presented as confirmed removed. Current status
SHALL identify the current workspace.

#### Scenario: Observe concurrent work

- **GIVEN** multiple checkouts belong to the bound repository
- **WHEN** workspace overview is requested
- **THEN** each observed checkout SHALL have separately attributed workflow state
- **AND** last-observed or unavailable information SHALL be labelled accurately

### Requirement: Fresh Guide binding for spawned worktree agents

An agent assigned to a separate workspace SHALL establish a fresh Guide interaction/session and explicitly bind the shared project root and assigned workspace root before workspace operations. Guide-provided spawning guidance SHALL NOT direct the new agent to reuse the parent session ID. A bound session identifier SHALL NOT be accepted to change that interaction's workspace; rejection SHALL preserve its original state. Existing configuration propagation SHALL NOT replace the workspace binding.

#### Scenario: Spawned agent binds its own checkout

- **GIVEN** a parent agent is bound to the main checkout and creates a linked worktree
- **WHEN** a new agent begins work in that checkout
- **THEN** it SHALL establish a distinct Guide session bound to that workspace and the shared project identity
- **AND** the parent session SHALL remain bound to its original workspace

#### Scenario: Reused session attempts workspace reassignment

- **GIVEN** a session is already bound to workspace A
- **WHEN** a request supplies that session identifier to bind workspace B
- **THEN** Guide SHALL reject the reassignment and request a fresh interaction
- **AND** workspace A's binding and workflow cache SHALL remain unchanged
