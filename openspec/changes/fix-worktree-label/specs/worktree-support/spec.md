# Spec Delta

## MODIFIED Requirements

### Requirement: Allocated worktree name

Guide SHALL allocate a readable non-`root` label only while a root-bound session initialises a new or previously unlabelled linked-worktree handoff. The root handoff SHALL create or initialise the target's effective configured basename-only `workflow-file` with that label before assigning a child. A bound linked-worktree session SHALL obtain its label only from that local file. Directory names and session binding SHALL NOT determine or mint labels.

#### Scenario: Linked worktree receives a generated name
- **GIVEN** a root-bound parent requests a new linked-worktree handoff
- **WHEN** Guide allocates the handoff
- **THEN** Guide assigns a readable worktree name
- **AND** instructs the parent to initialise the target's effective configured `workflow-file` with that name
- **AND** instructs the parent to record the name and path in shared handover context

#### Scenario: Allocated name is already in use
- **GIVEN** a parent holds the shared handover lock for a new linked worktree
- **AND** `worktrees.<allocated-name>` already exists
- **WHEN** the parent checks the allocated name
- **THEN** it SHALL release the lock without creating a worktree or changing handover context
- **AND** SHALL request another `guide://_worktree/new` allocation

#### Scenario: Existing worktree is resumed
- **GIVEN** a parent requests `guide://_worktree/use/<name>`
- **WHEN** the existing handover entry is read
- **THEN** its recorded absolute path SHALL be present in fresh Git worktree inventory
- **AND** it SHALL retain that name rather than allocate a replacement

#### Scenario: Child receives its worktree name
- **GIVEN** a shared handover entry contains a linked-worktree name and path
- **WHEN** a parent spawns the assigned child
- **THEN** the child receives the allocated name
- **AND** receives the absolute path and complete handover entry
- **AND** receives instructions to read its local workflow file before workflow operations
- **AND** resolves its intended path and task from the handover entry

#### Scenario: Existing linked worktree supplies its label

- **GIVEN** a linked worktree has its effective configured workflow file containing `worktree: existing-label`
- **WHEN** Guide first receives that workflow file for the bound session
- **THEN** the session SHALL adopt `existing-label`
- **AND** SHALL not use the checkout directory name to determine the label

#### Scenario: Unlabelled linked worktree receives a minted label

- **GIVEN** a root-bound parent selects an existing linked worktree with no effective configured workflow file or no `worktree` value
- **WHEN** Guide initialises handoff for that worktree
- **THEN** Guide SHALL mint a readable non-`root` label
- **AND** SHALL instruct the parent to write that label to the effective configured workflow file before spawning a child

#### Scenario: Child binding awaits workflow-file label

- **GIVEN** a child binds a linked worktree before Guide receives its effective configured workflow file
- **WHEN** the binding completes
- **THEN** Guide SHALL not allocate a replacement label
- **AND** SHALL direct the child to submit the effective configured workflow file to establish its label

### Requirement: Worktree-labelled workflow state

Each linked-worktree effective configured workflow file SHALL include its `worktree` label. Guide adopts the label on the first valid receipt and later receipts SHALL match it. The primary checkout defaults an omitted label to `root`. A linked-worktree session whose project workflow configuration is disabled SHALL still accept its initial valid workflow file so it can establish the required label.

#### Scenario: Agent reads its linked-worktree workflow file
- **GIVEN** a session is bound to a linked worktree named `languid_lizard`
- **WHEN** Guide receives that worktree's effective configured workflow file
- **THEN** it SHALL adopt and accept the file when `worktree` is `languid_lizard`
- **AND** SHALL reject a file labelled for a different worktree

#### Scenario: Initial label is adopted while project workflow is disabled
- **GIVEN** a session is bound to a linked worktree whose shared project has workflow disabled
- **AND** its effective configured workflow file contains a non-`root` worktree label
- **WHEN** Guide receives the valid workflow file
- **THEN** it SHALL adopt that label and begin workflow handling for the session
- **AND** SHALL not enable workflow in the shared project configuration

## ADDED Requirements

### Requirement: Root-only linked-worktree handoff

Guide SHALL allow `_worktree/new` only from a session bound to the repository root. A linked-worktree session SHALL be directed to return to a root-bound session for new-worktree handoff.

#### Scenario: Linked worktree requests new worktree
- **GIVEN** a session is bound to a linked worktree rather than the repository root
- **WHEN** it requests `guide://_worktree/new`
- **THEN** Guide SHALL not allocate a label or provide creation instructions
- **AND** SHALL direct the agent to use a root-bound session
