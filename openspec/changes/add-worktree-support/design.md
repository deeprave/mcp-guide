## Context

See proposal.md for motivation. Session currently retains one bound client root, which participates in configuration identity and filesystem resolution. Workflow state is cached by its TaskManager, but workflow paths resolve under the shared root. Separate sessions already receive shared durable configuration updates, but preservation of new session-local state must be verified.

## Goals / Non-Goals

**Goals:** Allow simultaneous sessions for linked worktrees to share configuration and documents while independently maintaining workflow and retain project-wide visibility of observed workspaces.

**Non-Goals:** Create or remove worktrees, merge branches, eliminate code conflicts, equate separate clones by remote URL, or add competing writers within one workspace. Existing OpenSpec storage policy is unchanged; audit its path assumptions without relocating artifacts automatically.

## Decisions

### Two roots with explicit scope

Extend initial project binding with optional `workspace_root`; `path` remains the project identity root and defaults workspace_root to itself for compatibility. Keep configuration identity `(name, bound_root_hash)` unchanged. Store workspace_root on Session, not in shared configuration. Each independent worktree agent establishes its own interaction. An existing Guide interaction/session ID must not be repurposed to select a different workspace. A worktree agent must establish a fresh Guide interaction and bind both project and assigned workspace roots; spawning instructions must not forward the parent session ID as reusable credentials. Guide rejects a workspace-change request carrying an already-bound session ID without altering its binding. Existing project selection follows fresh-Session switching semantics; config-name changes preserve the workspace when the project root is unchanged, whereas selecting a different project defaults workspace to its new root. Shared config publication preserves workspace binding and resets only affected derived state.

Expose `workspace_root`, project root, and resolved workflow path in template/request context. Do not silently reinterpret all existing relative paths. Relative workflow-file settings become workspace-relative; existing absolute settings remain explicit overrides, with a diagnostic when multiple workspaces share one workflow target. Code-facing guidance and git review/build/reset commands use workspace_root. Server docroot is unchanged.

### Client discovery and permissions

Obtain the checkout root and shared Git directory on the client. Resolve a relative common-directory result against the verified discovery directory; use its parent for ordinary repositories with a shared `.git` directory. Derive both roots without a remote URL. Retain the existing path-based identity rather than introducing a remote or common-directory hash that would orphan configuration. Separate clones remain separate projects. Unsupported layouts such as bare repositories or separate Git directories require an explicit identity root rather than guessing.

Use direct discovery only with verified filesystem sharing; otherwise request client-reported roots and checkout listings. Preserve lexical client-path handling, credentials and existing authorisation. An explicit workspace binding permits only the workspace access appropriate to existing project policy; it must not grant arbitrary sibling access. Validate the relationship when locally observable, reject a known mismatch, and otherwise retain a clearly client-reported relationship without claiming server verification.

### Workspace-local workflow

Resolve `.guide.yaml` against workspace_root, including direct-read bootstrap guidance. Do not fall back to the main checkout's workflow when a worktree file is absent. Bind workflow monitoring, cache keys, callbacks and file events to the owning Session and full resolved path; basename comparison is insufficient. No workflow state is published as project configuration. Workflow state is local runtime data and should be ignored by Git so a new checkout does not inherit another workspace's issue.

### Central overview is derived

Enumerate checkouts through client-side Git worktree listing and read their workflow files under authorised access. Provide `guide://_workspaces` to list workspace path, branch if available, issue, phase, and last observation. The current status identifies the current workspace. On remote servers, reports are last-observed snapshots with timestamps; inability to observe a path is not evidence of removal.

The server can enforce immutable binding for a supplied session ID, but a bearer identifier alone cannot prove which agent sent a request. Do not claim agent identity enforcement: fresh-session spawning guidance and workspace-binding checks prevent cross-workspace reuse, while a stronger caller-identity guarantee would require transport identity support.

## Risks / Trade-offs

- Two roots cause accidental path drift → centralise scoped resolvers and test workflow, documents and git-command guidance independently.
- Shared refresh overwrites local state → exercise simultaneous sessions and configuration updates.
- Client/server filesystem differences → preserve client-side discovery and lexical path handling; never run server Git against unverified client paths.

## Migration Plan

Keep omitted workspace_root compatible with current bindings. Relative workflow-file settings become workspace-relative without changing configuration identity. Update root-binding and workflow guidance together. Rollback restores the existing single-root workflow path behaviour; no configuration identity migration is needed.
