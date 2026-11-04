## 1. Binding and path scopes

- [ ] 1.1 Audit session/request binding, startup/root guidance, workflow paths, documents paths, OpenSpec and git-command path assumptions against the design; verify all affected consumers and existing spec contracts are accounted for before editing.
- [ ] 1.2 Add optional workspace_root to binding and preserve it through fresh-session selection and shared configuration publication; verify two sessions share configuration identity while retaining distinct workspace bindings, including omitted-workspace compatibility.
- [ ] 1.3 Add client-side repository/checkout discovery guidance and verified-filesystem discovery support; verify linked worktrees without remotes, independent clones, relative common-directory output and remote client paths resolve correctly without changing existing project hashes.
- [ ] 1.4 Introduce scoped path resolution and permission checks; verify workflows target workspace roots, documents/custom handover paths remain project-relative, and workspace binding does not grant unrelated sibling access.

## 2. Workflow isolation and context identity

- [ ] 2.1 Route workflow bootstrap, monitoring, caches and events by owning session and resolved workspace path; verify updates to identical filenames in separate workspaces do not cross-contaminate state and missing files do not fall back to the main checkout.
- [ ] 2.2 Add durable context registry and atomic name allocation with reserved root identity; verify concurrent allocation, restart recovery, unsafe names, copied-name conflicts and issue-free/workflow-disabled startup.
- [ ] 2.3 Persist optional context names in workspace workflow files and expose exact workflow/context paths to templates and guidance; verify agent replacement reuses the same handover without searching payload content.
- [ ] 2.4 Implement detached-context retention and explicit resume attachment; verify deletion preserves handover content, inaccessible paths are not treated as removed, recreated paths do not silently adopt old identities and live duplicate attachment is refused.

## 3. Handover and visibility

- [ ] 3.1 Resolve default handover guidance to shared context/<name>.json and preserve explicit overrides and opt-out; verify custom documents paths, write-policy checks and root.json default through rendered guidance.
- [ ] 3.2 Provide explicit non-destructive legacy context.json migration; verify legacy-only and both-files-present cases preserve existing files and never overwrite a destination.
- [ ] 3.3 Add client worktree discovery/reporting and guide://_workspaces overview, plus current workspace/context in status; verify separate issue/phase attribution, attachment states, timestamps and last-observed remote snapshots.
- [ ] 3.4 Update onboarding and developer/agent guidance for two roots, shared documents, context naming/resume and ignored local workflow state; verify rendered instructions use the correct paths for review/build/reset and handover operations.

## 4. Session ownership and retirement

- [ ] 4.1 Require fresh Guide interaction establishment in spawned worktree guidance and reject workspace reassignment through an existing bound session; verify rejection preserves parent state and a fresh child binding succeeds.
- [ ] 4.2 Implement a shared cross-process lock and atomic root handover update operation for every writer, including root-agent updates; verify concurrent root and workspace updates preserve all entries and unavailable client locking leaves files unchanged.
- [ ] 4.3 Implement explicit retirement with source-write serialisation, named root entries, durable commit-before-delete and registry updates; verify stale revisions, root-write failure, cleanup failure and crash/retry preserve context without duplication or loss.
- [ ] 4.4 Distinguish agent stop, unexpected checkout disappearance and explicit retirement in lifecycle guidance and overview; verify stop remains resumable, disappearance stays detached and retirement resolves to the consolidated named entry.

## 5. Integration validation

- [ ] 5.1 Exercise two independent sessions against temporary linked worktrees, including shared config changes, workflow edits, agent replacement and worktree removal/resumption; verify isolation and preserved handover end to end using observable behaviour, never source-text assertions.
- [ ] 5.2 Run focused pytest suites in a foreground terminal through completion, required project checks and strict OpenSpec validation; record results and remaining work in the configured handover context.
