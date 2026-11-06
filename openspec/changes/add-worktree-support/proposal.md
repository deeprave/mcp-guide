## Why

Independent agents in linked Git worktrees currently share a workflow file because Guide uses one repository root for both configuration identity and mutable workspace state. Agents need isolated workflow state while retaining shared project configuration and documents.

## What Changes

- Add a session-owned `workspace_root` alongside the existing repository identity root; preserve the existing project key and hash across linked worktrees.
- Resolve each session's workflow file against its workspace; retain `.todo/` and configured documents paths as shared project resources.
- Support client-side discovery when Guide cannot access the filesystem, without depending on a remote URL or treating independent clones as one project.
- Provide project-wide visibility by discovering Git checkouts and reporting workflow state and observation time.
- Require spawned worktree agents to establish fresh Guide sessions bound to their assigned checkout; prevent an existing session being repurposed for a different workspace.
- Preserve session workspace bindings during shared configuration publication and isolate workflow caches and events.

## Capabilities

### New Capabilities

- `worktree-support`: Separate project identity from workspace binding, isolate workflow state, and discover workspace activity centrally.

## Impact

Session and request binding APIs, root discovery guidance, path resolution and filesystem permissions, workflow monitoring and template context, shared configuration refresh, status output and tests. Existing single-checkout clients retain a default workspace equal to the project root. No remote service or new dependency is required. No implementation is included in this proposal.
