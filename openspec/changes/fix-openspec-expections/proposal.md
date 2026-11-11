# Proposal

## Why

Guide currently treats a worktree-local `openspec/` directory as proof that OpenSpec is available. OpenSpec itself resolves installations from ancestor directories and named stores, so that assumption rejects valid projects and couples Guide to client filesystem layout it cannot authoritatively inspect.

## What Changes

- Make OpenSpec CLI commands, run from the bound project, the sole authority for OpenSpec availability and project-store resolution.
- Remove OpenSpec enablement, cache invalidation, and rendered guidance that inspect or request `openspec/config.yaml`, `openspec/changes`, or other assumed worktree-relative OpenSpec paths.
- Cache change data from `openspec list --json` by its own TTL and explicit refreshes, rather than a client-reported directory modification time.
- Update onboarding, OpenSpec commands, and workflow guidance to consume CLI results and resolved paths instead of constructing paths beneath a presumed local `openspec/` directory.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-manager`: validate an enabled project through OpenSpec CLI results, without repository-asset probes.
- `template-context`: expose and refresh OpenSpec change data from CLI responses without worktree-local path assumptions.
- `cache-management`: invalidate OpenSpec change data through TTL and explicit refreshes rather than filesystem metadata.

## Impact

- `src/mcp_guide/openspec/task.py` and its event protocol
- OpenSpec, onboarding, and workflow Mustache templates
- OpenSpec task and template-context behavioural coverage
