## Why

Independent agents in linked Git worktrees currently share a workflow file because Guide uses one repository root for both configuration identity and mutable worktree state. Agents need isolated workflow state while retaining shared project configuration and documents.

## What Changes

- Add a session-owned `worktree` alongside the existing repository identity root; preserve the existing project key and hash across linked worktrees.
- Allocate a readable name for each new linked worktree. Direct the parent to store its name and path under `worktrees.<name>` in the client-owned shared handoff context, with unrelated global sections outside that map. For an existing linked worktree, its local workflow file is the authority for the name.
- Create each linked worktree as a sibling of the primary checkout at `{{project-name}}_{{worktree-name}}`.
- Resolve each session's workflow file against its worktree; retain the configured documents path as a shared project resource.
- Require the worktree name in linked-worktree workflow files so agents and reviewers can identify the file's owning worktree; the primary checkout may omit it and defaults to `root`.
- Support client-side discovery when Guide cannot access the filesystem, without depending on a remote URL or treating independent clones as one project.
- Provide `guide://_worktree/list` as the client-discovery entry point. It requests a Git worktree inventory through `send_file_content` using the `.git-worktrees.json` report path. Guide caches the snapshot for 90 seconds for worktree commands and refreshes it when absent, expired, or known stale after a worktree change.
- Make handoff context enabled by default unless `handoff-context` is explicitly `false`, and gate worktree commands on the resulting eligible handoff target; no separate worktree feature or project flag is introduced.
- Allow `guide://_worktree/list?verbose` to provide richer client-discovered checkout information. Guide derives workflow state from each readable worktree workflow file, never from handoff metadata.
- Require spawned worktree agents to establish fresh Guide sessions bound to their assigned checkout; prevent an existing session being repurposed for a different worktree.
- Detect a client-reported working-directory mismatch before worktree work begins, reject reuse of the existing session, and return fresh-binding guidance without forwarding the parent session identifier.
- Preserve session worktree bindings during shared configuration publication and isolate workflow caches and events.

## Capabilities

### New Capabilities

- `worktree-support`: Separate project identity from worktree binding, isolate workflow state, and discover worktree activity centrally.

## Impact

Session and request binding APIs, root discovery guidance, path resolution and filesystem permissions, workflow monitoring and template context, shared configuration refresh, the prominently documented handoff-context default and locking guidance, status output and tests. Existing single-checkout clients retain a default worktree equal to the project root. No remote service or new dependency is required. No implementation is included in this proposal.
