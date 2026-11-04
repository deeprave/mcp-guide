## Context

See proposal.md for motivation. Session currently retains one bound client root, which participates in configuration identity and filesystem resolution. Workflow state is cached by its TaskManager, but workflow paths resolve under the shared root. Documents default to `.todo/`; enabled handover guidance defaults to its single `context.json`. Separate sessions already receive shared durable configuration updates, but preservation of new session-local state must be verified.

## Goals / Non-Goals

**Goals:** Allow simultaneous sessions for linked worktrees to share configuration and documents while independently maintaining workflow; make the exact durable handover target discoverable before an issue is selected; retain central visibility after checkout deletion.

**Non-Goals:** Create or remove worktrees, merge branches, eliminate code conflicts, equate separate clones by remote URL, or add competing writers within one workspace. Existing OpenSpec storage policy is unchanged; audit its path assumptions without relocating artifacts automatically.

## Decisions

### Two roots with explicit scope

Extend initial project binding with optional `workspace_root`; `path` remains the project identity root and defaults workspace_root to itself for compatibility. Keep configuration identity `(name, bound_root_hash)` unchanged. Store workspace_root on Session, not in shared configuration. Each independent worktree agent establishes its own interaction. An existing Guide interaction/session ID must not be repurposed to select a different workspace. A worktree agent must establish a fresh Guide interaction and bind both project and assigned workspace roots; spawning instructions must not forward the parent session ID as reusable credentials. Guide rejects a workspace-change request carrying an already-bound session ID without altering its binding. Existing project selection follows fresh-Session switching semantics; config-name changes preserve the workspace when the project root is unchanged, whereas selecting a different project defaults workspace to its new root. Shared config publication preserves workspace binding and resets only affected derived state.

Expose `workspace_root`, project root, resolved workflow path, context name and exact handover path in template/request context. Do not silently reinterpret all existing relative paths. Documents and explicit handover overrides remain project-relative. Relative workflow-file settings become workspace-relative; existing absolute settings remain explicit overrides, with a diagnostic when multiple workspaces share one workflow target. Code-facing guidance and git review/build/reset commands use workspace_root. Server docroot is unchanged.

### Client discovery and permissions

Obtain the checkout root and shared Git directory on the client. Resolve a relative common-directory result against the verified discovery directory; use its parent for ordinary repositories with a shared `.git` directory. Derive both roots without a remote URL. Retain the existing path-based identity rather than introducing a remote or common-directory hash that would orphan configuration. Separate clones remain separate projects. Unsupported layouts such as bare repositories or separate Git directories require an explicit identity root rather than guessing.

Use direct discovery only with verified filesystem sharing; otherwise request client-reported roots and checkout listings. Preserve lexical client-path handling, credentials and existing authorisation. An explicit workspace binding permits only the workspace access appropriate to existing project policy; it must not grant arbitrary sibling access. Validate the relationship when locally observable, reject a known mismatch, and otherwise retain a clearly client-reported relationship without claiming server verification.

### Workspace-local workflow

Resolve `.guide.yaml` against workspace_root, including direct-read bootstrap guidance. Do not fall back to the main checkout's workflow when a worktree file is absent. Bind workflow monitoring, cache keys, callbacks and file events to the owning Session and full resolved path; basename comparison is insufficient. No workflow state is published as project configuration. Workflow state is local runtime data and should be ignored by Git so a new checkout does not inherit another workspace's issue or context name.

### Durable context names in shared documents

Store default context at `<documents>/context/<name>.json`. Reserve `root` for the main checkout (also the single workspace of a non-Git project). Allocate a filesystem-safe generated name once per linked workspace and persist it as optional `context: <name>` in its workflow file. A project-scoped durable registry maps names to workspace paths and observation metadata. Put the registry under `<documents>/context/`, separate from handover payloads; allocate names using locking and atomic writes to prevent cross-session/process collisions. Session IDs, issues, branch names and directory basenames are not durable context identities.

Register/recover a workspace mapping before queueing handover guidance. This also works when workflow behaviour is disabled: the registry supplies the mapping without requiring workflow activation; mirror it in the workflow file when enabled. Reject unsafe names and conflicting copied context names instead of silently overwriting another workspace's handover. Templates and tools provide the exact resolved target, avoiding searches through issue directories. Existing custom handoff targets retain their explicit semantics and may intentionally be shared.

Unexpected removal or pruning marks a context detached and retains its handover and registry entry. Explicit retirement follows the consolidation protocol below; stopping or replacing an agent alone is not retirement. Recreating a directory must not automatically claim an old detached context. Explicit resumption attaches a selected detached context to a new workspace, updates the mapping and workflow reference, and preserves its content. Refuse attachment to two live workspaces by default. Replacing an agent/session in an existing workspace reuses the established name.

### Central overview is derived

Enumerate checkouts through client-side Git worktree listing and read their workflow files under authorised access. Provide `guide://_workspaces` to list workspace path, branch if available, issue, phase, context name, resolved handover path, attachment and last observation. The current status identifies the current workspace and context. Distinguish attached/detached and unavailable/unknown rather than guessing staleness from payload content. On remote servers, reports are last-observed snapshots with timestamps; inability to observe a path is not evidence of removal.

### Root handover locking and explicit retirement

All writes to shared `context/root.json`, including ordinary root-agent handover updates, must use the same cross-process lock and atomic read-modify-write path. Agent instructions must route these updates through Guide-managed operations rather than direct file edits; atomic replacement alone does not prevent lost updates. With a remote client filesystem, execute locking and mutation on that client through a supported client operation; do not substitute an unrelated server-local lock. If that capability is unavailable, report the limitation and leave context files intact.

Explicit worktree retirement acquires the root lock, reads the latest root and final workspace handover, and preserves the workspace payload under a named entry such as `workspaces.<context-name>`. Preserve root-owned fields and every other workspace entry. Record source context identity and revision/digest so retries can recognise a previously committed consolidation. Serialise retirement against writes to the retiring workspace context as well, marking it closing before taking the final snapshot. Reject or retry stale source revisions; never delete a newer source payload.

Commit and durably persist the root update before removing the original workspace context. Then mark the registry entry retired/consolidated. If root writing fails, keep the original. If cleanup fails after commit, retain retry information and perform idempotent cleanup without duplicate entries or loss. A replacement root-agent update must preserve consolidated workspace entries. Lock contention and crash recovery must be explicit; do not break another live owner's lock on an arbitrary timeout.

An agent stopping, disconnecting or being replaced retains the separate context and attachment. Confirmed unexpected worktree removal retains a detached context until explicit retirement or resume. Explicit retirement consolidates and removes the original only after successful persistence, preserving the durable name and consolidated location for central lookup. This distinguishes resumable work from completed workspace lifecycle.

The server can enforce immutable binding for a supplied session ID, but a bearer identifier alone cannot prove which agent sent a request. Do not claim agent identity enforcement: fresh-session spawning guidance and workspace-binding checks prevent cross-workspace reuse, while a stronger caller-identity guarantee would require transport identity support.

## Risks / Trade-offs

- Two roots cause accidental path drift → centralise scoped resolvers and test workflow, documents and git-command guidance independently.
- Shared refresh overwrites local state → exercise simultaneous sessions and configuration updates.
- Registry races or copied workflow files reuse a name → atomic allocation, conflict diagnostics and explicit resume.
- Worktree deletion removes local references → preserve central registry and handover; distinguish confirmed removal from inaccessible paths.
- Existing default handover occupies `.todo/context.json` → explicit non-destructive migration to `context/root.json`; never overwrite either file or merge contexts automatically.
- Client/server filesystem differences → preserve client-side discovery and lexical path handling; never run server Git against unverified client paths.

## Migration Plan

Keep omitted workspace_root compatible with current bindings. Introduce registry and named defaults without deleting legacy handover files. If only the old default exists, offer an explicit migration copying it to `context/root.json`; if both exist, report the conflict and leave both intact. During transition identify the legacy target clearly until migration is selected. Custom targets and disabled handover remain unchanged. Update root-binding, workflow and handover guidance together. Rollback preserves central handovers and leaves new registry data unused; no configuration identity migration is needed.
