## 1. Worktree discovery and handoff

- [x] 1.1 Make `handoff-context` default to the shared context target unless explicitly `false`, document that exception in feature-flag guidance, and implement `guide://_worktree/list`, `guide://_worktree/new`, and `guide://_worktree/use` against the resulting eligible target; obtain the client Git worktree inventory through `.git-worktrees.json`, cache it for 90 seconds, allocate readable names, and return the parent/child handoff instructions.
- [x] 1.2 Create new linked worktrees as primary-checkout siblings named `{{project-name}}_{{worktree-name}}`; elicit branch selection when absent, check out existing branches, create new branches from `main`, and direct the parent to store the assigned path, task metadata, starting phase, plan, and instructions under `worktrees.<name>` while preserving global context sections.

## 2. Session binding and permissions

- [x] 2.1 Add the optional `worktree` binding alongside the project identity root, preserve it through configuration publication, and forbid worktree reassignment of a bound session.
- [x] 2.2 Add client working-directory preflight and fresh-session guidance; bind a child to its handoff-provided worktree name without forwarding the parent session identifier.
- [x] 2.3 Resolve authorised client paths against the bound worktree while preserving shared project configuration and documents access without granting arbitrary sibling access.

## 3. Worktree-local state

- [x] 3.1 Implement and render the client-side shared-context update: worktree-labelled lock, 90-second lock modification-time inactivity, reread/validation, merge-own-entry, atomic replacement, and lock removal.
- [x] 3.2 Make workflow bootstrap, parsing, monitoring, caches, events, review artefacts, status, and Git guidance worktree-aware; require matching `worktree` state in linked-worktree workflow files and default an omitted primary value to `root`.
- [x] 3.3 Keep handoff client-owned: never request or consume it in Guide. Make active inventory paths readable for the project and derive any verbose worktree state from worktree-local workflow files.

## 4. Review corrections

- [x] 4.1 Resolve linked-worktree labels solely from the local workflow file, minting a label only when that file is absent or unlabelled; never infer identity from the checkout directory name.
- [x] 4.2 Separate runtime-derived default paths from persisted user-added permissions, derive linked-worktree access to the checkout and root-scoped shared resources centrally, and render both `path.documents` and `documents-path` as root-based paths with one trailing slash.
- [x] 4.3 Remove obsolete completed-item directory guidance from templates and add regression coverage for the corrected worktree and path behaviour.
- [x] 4.4 Pass the allocated name, absolute path, and complete handoff entry to a spawned child; require it to establish that name in its local workflow file before submitting workflow state to its fresh session.
- [x] 4.5 Expand readable-name entropy and require `_worktree/new` to check the locked handoff map for an allocated-name collision before creating a worktree; retain an existing name only through `_worktree/use`.
- [x] 4.6 Require `_worktree/use` to resolve its existing named handoff entry and verify the recorded absolute path against fresh Git worktree inventory before handing it to a child.
- [x] 4.7 Accept every recognised workflow phase, including a phase outside the configured guidance sequence; continue rejecting malformed YAML and unknown or schema-invalid state.
- [x] 4.8 Expose only fresh client-reported worktree inventory in template context, invalidating cached context after replacement or expiry.
- [x] 4.9 Centralise session-aware path authorisation so runtime defaults and persisted static paths are combined for enforcement while only static paths remain project configuration.
