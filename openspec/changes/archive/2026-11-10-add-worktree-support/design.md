## Context

See proposal.md for motivation. Session currently retains one bound client root, which participates in configuration identity and filesystem resolution. Workflow state is cached by its TaskManager, but workflow paths resolve under the shared root. Separate sessions already receive shared durable configuration updates, but preservation of new session-local state must be verified.

## Goals / Non-Goals

**Goals:** Allow simultaneous sessions for linked worktrees to share configuration and documents while independently maintaining workflow and retain project-wide visibility of observed worktrees.

**Non-Goals:** Direct server-side Git operations on the client filesystem, worktree removal, merge branches, elimination of code conflicts, equating separate clones by remote URL, or competing writers within one worktree. Existing OpenSpec storage policy is unchanged; audit its path assumptions without relocating artifacts automatically.

## Decisions

### Two roots with explicit scope

Extend initial project binding with optional `worktree`; `path` remains the project identity root and defaults worktree to itself for compatibility. Keep configuration identity `(name, bound_root_hash)` unchanged. Store worktree on Session, not in shared configuration. Each independent worktree agent establishes its own interaction. An existing Guide interaction/session ID must not be repurposed to select a different worktree. A worktree agent must establish a fresh Guide interaction and bind both the project root and assigned worktree; spawning instructions must not forward the parent session ID as reusable credentials. Guide rejects a worktree-change request carrying an already-bound session ID without altering its binding. Existing project selection follows fresh-Session switching semantics; config-name changes preserve the worktree when the project root is unchanged, whereas selecting a different project defaults worktree to that project's root. Shared config publication preserves worktree binding and resets only affected derived state.

Expose `worktree`, project root, and resolved workflow path in template/request context. Do not silently reinterpret all existing relative paths. Relative workflow-file settings become worktree-relative; existing absolute settings remain explicit overrides, with a diagnostic when multiple worktrees share one workflow target. Code-facing guidance and git review/build/reset commands use worktree. Server docroot is unchanged.

### Allocated worktree names and shared handover context

`guide://_worktree/new` allocates a readable worktree name before the linked worktree exists. The name and resulting path are stored in the shared handover context; Guide does not maintain a separate worktree registry. Before creating the worktree, the parent holds the client-side context lock and checks whether `worktrees.<allocated-name>` already exists. A collision releases the lock without changing the handover or creating a worktree, then requests another allocation. The parent retains the lock through creation and the atomic handover update, preventing a concurrent allocation from reusing the same key. The parent passes that allocated label to the child, which resolves its intended path and task from the handover record. For an existing linked worktree, `guide://_worktree/use` requires the named handover entry and its recorded absolute path to be present in fresh Git inventory, then resumes that name rather than allocating another. Its local workflow file supplies the label when the child binds. The primary checkout is `root` when a label is needed.

Keep handover context in the shared documents target, ordinarily `.todo/context.json`. It is client-owned and Guide neither requests, reads, caches, nor uses it as workflow state. Reserved top-level sections hold global handover information, such as a todo note or ancillary data. Worktree-specific state is nested under `worktrees.<name>`. Each agent updates only its own map entry and preserves every global key and other worktree entry. The primary checkout uses `worktrees.root`. Review artefacts use the same worktree name together with the issue name to avoid collisions between independent worktrees. The workflow file remains worktree-rooted.

Because the shared context file resides on the client filesystem, its update protocol must be client-side. The adjacent lock file names the holding worktree. Its modification time is the sole activity signal: a lock older than 90 seconds is inactive and may be replaced. A client creates the lock, rereads and validates the current JSON, merges only its worktree entry, atomically replaces the document, then removes the lock. The handoff instruction must state this simple protocol; do not assume the Guide server can operate on a remote client path.

`handoff-context` is enabled by default: an absent value resolves to the normal shared context target. Only an explicit `false` disables it. Worktree commands rely on the resulting eligible handover target; no separate worktree feature or project flag is introduced. The feature-flags specification must present this exception prominently because it differs from flags whose absence means no value.

### Fresh worktree session preflight

Before a spawned agent begins work in an assigned worktree, it reports its current directory through the existing client working-directory signal. Guide compares the discovered or client-reported worktree with the session binding. A mismatch never changes the existing session: Guide returns instructions to establish a fresh interaction with `set_project(path=<project root>, worktree=<current worktree>)` and no inherited session identifier.

Guide cannot establish that a bearer session identifier was sent by a particular agent. The preflight and immutable worktree binding prevent accidental reuse, while transport-level caller identity would be required to prevent a malicious caller from using another agent's identifier. Spawn guidance must therefore instruct the parent not to forward its session identifier and the child to perform the preflight before any worktree operation.

### Client discovery and permissions

Obtain the checkout root and shared Git directory on the client. Resolve a relative common-directory result against the verified discovery directory; use its parent for ordinary repositories with a shared `.git` directory. Derive both roots without a remote URL. Retain the existing path-based identity rather than introducing a remote or common-directory hash that would orphan configuration. Separate clones remain separate projects. Unsupported layouts such as bare repositories or separate Git directories require an explicit identity root rather than guessing.

Use direct discovery only with verified filesystem sharing; otherwise request client-reported roots and checkout listings. Preserve lexical client-path handling, credentials and existing authorisation. An explicit worktree binding permits only the worktree access appropriate to existing project policy; it must not grant arbitrary sibling access. Validate the relationship when locally observable, reject a known mismatch, and otherwise retain a clearly client-reported relationship without claiming server verification.

`guide://_worktree/list` is the client-discovery entry point. It instructs the agent to obtain the current Git worktree list and send the resulting inventory through `send_file_content` with path `.git-worktrees.json`. The report is client-provided discovery data, not a project file that Guide writes. Guide retains it for 90 seconds in the bound session; worktree commands require a current snapshot and request refresh when it is absent, expired, or known stale after a worktree change.

`guide://_worktree/new` accepts the intended handoff metadata, allocates a name before the linked worktree exists, and returns instructions to create its sibling path as `{{project-name}}_{{worktree-name}}`. For example, a root checkout at `/Users/davidn/Code/mcp-guide` with name `ludicrous-naming` creates `/Users/davidn/Code/mcp-guide_ludicrous-naming`. The parent records its handoff at `worktrees.<name>`. The command elicits branch selection when no branch is supplied: an existing selected branch is checked out, while a new branch is created from `main`, never from the primary checkout's current branch. `guide://_worktree/use` directs the parent to read the existing client handoff record after a fresh inventory and pass the corresponding child handoff. The parent gives the child its allocated name, absolute path, and complete handoff entry, never the parent session identifier. Before the child binds, it initialises its local workflow file with the allocated `worktree` label; the first submitted workflow state then causes the fresh session to adopt that same label.

### Worktree-local workflow

Resolve a basename-only `.guide.yaml` setting against the bound worktree, including direct-read bootstrap guidance. An absolute or directory-qualified workflow-file disables worktree support. Do not fall back to the main checkout's workflow when a worktree file is absent. File submissions use the workflow-file basename and are scoped to the owning Session. No workflow state is published as project configuration. Workflow state is local runtime data and should be ignored by Git so a new checkout does not inherit another worktree's issue.

Every linked-worktree workflow file includes `worktree: <name>`. The value identifies the owning worktree for agents and reviewers. If an existing file has a label, Guide adopts it on first receipt; if it lacks one, the agent adds the newly allocated session label before submitting it. Later receipts must match the adopted label. The primary checkout may omit the field, which defaults to `root`; a child uses its client handoff entry to initialise a new file.

### Worktree list is derived

Enumerate checkouts through client-side Git worktree listing. The reported active checkout paths become permitted read roots for that project; `guide://_worktree/list?verbose` may read their workflow files to report observed state. It never uses handoff metadata as a source. On remote servers, reports are client-provided observations; inability to observe a path is not evidence of removal.

The server can enforce immutable binding for a supplied session ID, but a bearer identifier alone cannot prove which agent sent a request. Do not claim agent identity enforcement: fresh-session spawning guidance and worktree-binding checks prevent cross-worktree reuse, while a stronger caller-identity guarantee would require transport identity support.

## Risks / Trade-offs

- Two roots cause accidental path drift → centralise scoped resolvers and test workflow, documents and git-command guidance independently.
- Shared refresh overwrites local state → exercise simultaneous sessions and configuration updates.
- Client/server filesystem differences → preserve client-side discovery and lexical path handling; never run server Git against unverified client paths.

## Migration Plan

Keep omitted worktree compatible with current bindings. Relative workflow-file settings become worktree-relative without changing configuration identity. Update root-binding and workflow guidance together. Rollback restores the existing single-root workflow path behaviour; no configuration identity migration is needed.
