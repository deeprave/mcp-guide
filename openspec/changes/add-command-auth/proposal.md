# Proposal

## Why

`add-mcp-authentication` correctly identifies command resources and prompt commands as potential authorisation boundaries, but Guide commands principally render instructions for a client to perform separately protected tool operations. Adding a user-scope gate without establishing a direct server-side mutation would unnecessarily prevent unauthenticated callers from using help, inspection, and onboarding guidance.

This change establishes whether any command-rendering path performs a security-relevant direct mutation. It keeps the two command entry points aligned and introduces enforcement only where the audit proves it is needed.

## What Changes

- Audit the shared `handle_command()` path, command rendering, and command-specific pre-render work for direct server-side mutations and classify each observed effect.
- Preserve unauthenticated command rendering where a command only reads, renders guidance, queues session-local work, or instructs the client to invoke separately protected tools.
- If a command directly performs a protected mutation, require an explicit, server-owned `AuthScope` declaration and enforce it in the shared command route before that action.
- Ensure an enforced command scope has identical behaviour whether reached through a `guide://_...` resource URI or the Guide prompt command syntax.
- Document that command templates do not define or weaken access policy; templates may guide callers using request-scoped `auth` predicates, while the server owns any actual command authorisation decision.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `prompt-infrastructure`: define the authorisation boundary for prompt-dispatched commands without gating ordinary prompt content or inspection.
- `mcp-resources-guide-scheme`: define the same authorisation behaviour for command resource URIs and tool-backed command URI resolution.

## Impact

- Command routing in `src/mcp_guide/prompts/guide_prompt.py` and command URI resolution in `src/mcp_guide/tools/tool_resource.py`.
- Deferred prompt/resource registration only if the audit establishes that their public boundary must carry an explicit command scope.
- Authentication contracts and ADR-014 may need clarifying language, but this change does not add an authentication provider, token format, principal model, transport policy, or template-configurable access policy.
- Behavioural tests must exercise both command routes and prove that rendering alone does not gain or lose access incorrectly.
