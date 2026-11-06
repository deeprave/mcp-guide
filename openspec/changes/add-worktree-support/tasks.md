## 1. Binding and path scopes

- [ ] 1.1 Audit session/request binding, workflow paths, OpenSpec and git-command path assumptions against the design; verify all affected consumers and existing spec contracts are accounted for before editing.
- [ ] 1.2 Add optional workspace_root to binding and preserve it through fresh-session selection and shared configuration publication; verify two sessions share configuration identity while retaining distinct workspace bindings, including omitted-workspace compatibility.
- [ ] 1.3 Add client-side repository/checkout discovery guidance and verified-filesystem discovery support; verify linked worktrees without remotes, independent clones, relative common-directory output and remote client paths resolve correctly without changing existing project hashes.
- [ ] 1.4 Introduce scoped path resolution and permission checks; verify workflows target workspace roots and workspace binding does not grant unrelated sibling access.

## 2. Workflow isolation

- [ ] 2.1 Route workflow bootstrap, monitoring, caches and events by owning session and resolved workspace path; verify updates to identical filenames in separate workspaces do not cross-contaminate state and missing files do not fall back to the main checkout.
- [ ] 2.2 Add client worktree discovery/reporting and `guide://_workspaces` overview, plus the current workspace in status; verify separate issue/phase attribution, timestamps and last-observed remote snapshots.
- [ ] 2.3 Update onboarding and developer/agent guidance for workspace binding and ignored local workflow state; verify rendered instructions use the correct paths for review, build, and reset operations.

## 3. Session ownership

- [ ] 3.1 Require fresh Guide interaction establishment in spawned worktree guidance and reject workspace reassignment through an existing bound session; verify rejection preserves parent state and a fresh child binding succeeds.

## 4. Integration validation

- [ ] 4.1 Exercise two independent sessions against temporary linked worktrees, including shared config changes and workflow edits; verify isolation using observable behaviour, never source-text assertions.
