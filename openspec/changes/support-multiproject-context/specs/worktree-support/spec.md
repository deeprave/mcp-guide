# Spec Delta

## MODIFIED Requirements

### Requirement: Allocated worktree name

Guide SHALL allocate a readable name for a new linked-worktree handoff and record it with the path in the current Guide project's shared handover namespace. Existing worktrees use their local workflow-file label. Directory names SHALL NOT determine labels or project configuration identity.

#### Scenario: Linked worktree receives a generated name
- **GIVEN** a parent requests a new linked-worktree handoff
- **WHEN** Guide allocates the handoff
- **THEN** Guide assigns a readable worktree name
- **AND** instructs the parent to record the name and path in its project's shared handover namespace

#### Scenario: Allocated name is already in use
- **GIVEN** a parent holds the shared handover lock for a new linked worktree
- **AND** `projects.<project-name>.worktrees.<allocated-name>` already exists
- **WHEN** the parent checks the allocated name
- **THEN** it SHALL release the lock without creating a worktree or changing handover context
- **AND** SHALL request another `guide://_worktree/new` allocation

#### Scenario: Existing worktree is resumed
- **GIVEN** a parent requests `guide://_worktree/use/<name>`
- **WHEN** the existing handover entry is read from `projects.<project-name>.worktrees.<name>`
- **THEN** its recorded absolute path SHALL be present in fresh Git worktree inventory
- **AND** it SHALL retain that name rather than allocate a replacement

#### Scenario: Child receives its worktree name
- **GIVEN** a shared handover entry contains a linked-worktree name and path
- **WHEN** a parent spawns the assigned child
- **THEN** the child receives the allocated name
- **AND** receives the absolute path and complete handover entry
- **AND** initialises its local workflow file with `worktree: <allocated-name>` before submitting workflow state
- **AND** resolves its intended path and task from the handover entry

#### Scenario: Existing linked worktree supplies its label

- **GIVEN** a linked worktree has a local workflow file containing `worktree: existing-label`
- **WHEN** Guide first receives that workflow file for the bound session
- **THEN** the session SHALL adopt `existing-label`
- **AND** SHALL not use the checkout directory name to determine the label

#### Scenario: Unlabelled linked worktree receives a minted label

- **GIVEN** a linked worktree has no local workflow file or its workflow file has no `worktree` value
- **WHEN** Guide initialises workflow guidance for that session
- **THEN** Guide SHALL mint a readable non-`root` label
- **AND** SHALL instruct the agent to write that label to the local workflow file

### Requirement: Shared handover context is worktree-keyed

Worktree-specific handover data SHALL be stored at `projects.<project-name>.worktrees.<worktree-name>` in the shared context object. Reserved top-level sections MAY contain global todo notes or ancillary information and SHALL be preserved. The primary checkout SHALL use the `root` worktree label within its own project namespace.

#### Scenario: Concurrent worktree handovers
- **GIVEN** two linked-worktree sessions update shared handover context for one project
- **WHEN** each writes its `projects.<project-name>.worktrees.<worktree-name>` entry
- **THEN** each worktree entry is preserved
- **AND** neither update replaces the other worktree entry

#### Scenario: Separate projects share handover context
- **GIVEN** independently configured projects use the same structured handover document
- **WHEN** each primary checkout updates its `root` worktree entry
- **THEN** each update SHALL use that project's own `projects.<project-name>` namespace
- **AND** neither project SHALL replace the other's handover state

#### Scenario: Root handover preserves global information
- **GIVEN** shared context contains reserved global sections
- **WHEN** the primary checkout updates its `projects.<project-name>.worktrees.root` handover entry
- **THEN** Guide SHALL preserve the global sections
- **AND** SHALL not replace another project or worktree entry

### Requirement: Client context updates are locked and atomic

The client SHALL create an adjacent context lock, reread and validate the document, merge only the caller's project/worktree entry, atomically replace the document, and remove the lock.

#### Scenario: Client updates one worktree entry
- **GIVEN** a client holds the context lock for its project and worktree
- **WHEN** it updates handover context
- **THEN** it SHALL preserve other project and worktree entries
- **AND** SHALL atomically replace the context document before releasing its lock

### Requirement: Context locks use modification time

A context lock SHALL identify the holding project and worktree. Its modification time SHALL be the sole activity signal. A lock older than 90 seconds is inactive and may be replaced.

#### Scenario: Client replaces an inactive lock
- **GIVEN** an adjacent context lock is older than 90 seconds
- **WHEN** a client needs to update context
- **THEN** it SHALL replace the inactive lock
