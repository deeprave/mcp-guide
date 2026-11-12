# Proposal

## Why

Guide currently treats a worktree-local `openspec/` directory as proof that OpenSpec is available. Guide must not validate, infer, or inspect a project's OpenSpec store at all: the OpenSpec CLI is its only interface to OpenSpec data and operations.

## What Changes

- Make OpenSpec CLI commands, run from the active session worktree when data or an operation is needed, Guide's sole interface to OpenSpec.
- Remove OpenSpec enablement, cache invalidation, and rendered guidance that inspect or request `openspec/config.yaml`, `openspec/changes`, or other assumed worktree-relative OpenSpec paths.
- Cache change data from `openspec list --json` by its own TTL and explicit refreshes, rather than a client-reported directory modification time or a preflight store check.
- Update onboarding, OpenSpec commands, and workflow guidance to consume CLI results and resolved paths instead of constructing paths beneath a presumed local `openspec/` directory.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-manager`: keep enabled-project startup passive and obtain OpenSpec CLI results only for an on-demand consumer, without repository-asset probes or store validation.
- `template-context`: expose and refresh OpenSpec change data from CLI responses without worktree-local path assumptions.
- `cache-management`: invalidate OpenSpec change data through TTL and explicit refreshes rather than filesystem metadata.

## Impact

- `src/mcp_guide/openspec/task.py` and its event protocol
- OpenSpec, onboarding, and workflow Mustache templates
- OpenSpec task and template-context behavioural coverage
