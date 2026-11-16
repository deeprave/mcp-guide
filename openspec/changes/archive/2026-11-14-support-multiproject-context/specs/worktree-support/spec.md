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

#### Scenario: Root initialises an unlabelled linked worktree

- **GIVEN** a linked worktree has no local workflow file or its workflow file has no `worktree` value
- **WHEN** a root-bound session prepares that worktree through `guide://_worktree/use`
- **THEN** Guide SHALL allocate a readable non-`root` label
- **AND** SHALL instruct the root agent to write that label to the target local workflow file before child handoff
- **AND** the child session SHALL retain and submit the prepared label

### Requirement: Shared handover context is worktree-keyed

Worktree-specific handover data SHALL be stored at `projects.<project-name>.worktrees.<worktree-name>` in the shared context object. Every worktree entry SHALL include a `timestamp` recording the entry's date and time, and a `path` recording the worktree path. `issue` and `phase` MAY be included but are not required because workflow state is tracked separately. Beyond the required bookkeeping fields, an entry MAY contain any valid JSON necessary for a complete, agent-agnostic handoff, including nested objects and lists; agents SHALL remove information once it is no longer relevant. Reserved top-level sections MAY contain genuinely global todo notes or instructions and SHALL be preserved. The primary checkout SHALL use the `root` worktree label within its own project namespace. Projects sharing one context object SHALL use distinct configured Guide project names.

#### Scenario: Worktree handover records resumable state
- **GIVEN** a client updates its worktree handover entry
- **WHEN** it writes `projects.<project-name>.worktrees.<worktree-name>`
- **THEN** the entry SHALL include its `timestamp` and `path`
- **AND** it MAY include information needed to resume work
- **AND** it SHALL NOT require `issue` or `phase`

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

#### Scenario: Worktree handover contains complete current context
- **GIVEN** a client updates its worktree handover entry
- **WHEN** it records current handover context beyond `timestamp` and `path`
- **THEN** it MAY use any valid JSON structure needed for another agent or session to resume work
- **AND** it SHALL remove information that is no longer relevant

#### Scenario: Shared projects have distinct names
- **GIVEN** separate Guide projects share one structured handover document
- **WHEN** they update their project namespaces
- **THEN** each project SHALL have a distinct configured project name
- **AND** projects with the same configured name SHALL NOT be treated as separate namespaces

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

## ADDED Requirements

### Requirement: Legacy handover context is migrated without loss

Guide SHALL preserve legacy `worktrees` entries while merging an applicable current-project entry into the current project namespace under the context lock. Where a legacy and namespaced entry overlap, it SHALL retain the entry with the newer timestamp. It SHALL treat legacy root-level handover state as the current project's `root` worktree context, except for genuinely global root data. Migration guidance SHALL be one concise, complete paragraph without examples or embellishment.

#### Scenario: Legacy worktree entry is retained during migration
- **GIVEN** a shared handover document contains a legacy `worktrees.<label>` entry for the current project
- **WHEN** the client migrates that entry
- **THEN** it SHALL write the entry to `projects.<project-name>.worktrees.<label>`
- **AND** SHALL preserve the legacy `worktrees` mapping and unrelated entries

#### Scenario: Legacy root context is migrated
- **GIVEN** a shared handover document contains current-project handover state at its root
- **WHEN** the client migrates that state
- **THEN** it SHALL write the state to `projects.<project-name>.worktrees.root`
- **AND** SHALL preserve genuinely global root data

#### Scenario: Legacy and namespaced entries overlap
- **GIVEN** a legacy worktree entry and its namespaced entry both exist
- **WHEN** the client migrates the legacy entry
- **THEN** it SHALL retain the entry with the newer timestamp

### Requirement: Review requests preserve handover context

A review request SHALL NOT update handover context. It SHALL change workflow state only when the workflow phase is not already `review`.

#### Scenario: Review starts outside the review phase
- **GIVEN** a review request arrives while workflow phase is not `review`
- **WHEN** the review begins
- **THEN** the client SHALL set workflow phase to `review`
- **AND** SHALL not otherwise alter workflow state or handover context

#### Scenario: Review starts in the review phase
- **GIVEN** a review request arrives while workflow phase is `review`
- **WHEN** the review begins
- **THEN** the client SHALL not alter workflow state or handover context
