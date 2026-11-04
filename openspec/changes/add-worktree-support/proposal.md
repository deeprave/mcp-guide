## Why

Independent agents in linked Git worktrees currently share a workflow file and handover context because Guide uses one repository root for both configuration identity and mutable workspace state. Agents need isolated workflow state while retaining shared project configuration, shared documents and durable handover information that survives worktree removal.

## What Changes

- Add a session-owned `workspace_root` alongside the existing repository identity root; preserve the existing project key and hash across linked worktrees.
- Resolve each session's workflow file against its workspace; retain `.todo/` and configured documents paths as shared project resources.
- Support client-side discovery when Guide cannot access the filesystem, without depending on a remote URL or treating independent clones as one project.
- Allocate stable context names for workspaces, use `root` for the main checkout, and resolve handover files under the shared documents directory at `context/<name>.json`.
- Persist context names in workspace workflow state, preserve detached contexts after worktree deletion, and support explicit resumption from another workspace.
- Provide project-wide visibility by discovering Git checkouts and reporting workflow state, context attachment and observation time.
- Require spawned worktree agents to establish fresh Guide sessions bound to their assigned checkout; prevent an existing session being repurposed for a different workspace.
- Serialise all root handover updates with a cross-process lock; on explicit worktree retirement, preserve its handover as a named entry in root.json before removing the original workspace context. Agent stops alone retain resumable context.
- Preserve session workspace bindings during shared configuration publication and isolate workflow caches and events.

## Capabilities

### New Capabilities

- `worktree-support`: Separate project identity from workspace binding, isolate workflow state, and discover workspace activity centrally.

### Modified Capabilities

- `handover-context`: Resolve default handover targets through durable workspace context names within the shared documents directory.

## Impact

Session and request binding APIs, root discovery guidance, path resolution and filesystem permissions, workflow monitoring and template context, shared configuration refresh, handover startup guidance, status output and tests. Existing single-checkout clients retain a default workspace equal to the project root. Existing explicit handover targets remain supported. No remote service or new dependency is required. No implementation is included in this proposal.
