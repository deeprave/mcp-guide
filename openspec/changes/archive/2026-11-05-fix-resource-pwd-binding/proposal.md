# Proposal

## Why

An opted-in stdio client with a verified shared inherited `PWD` can bootstrap a project through tools and prompts, but its first native `resources/read` request is rejected before the shared bootstrap runs. This prevents agents that begin with `guide://_status` from using the intended PWD shortcut.

## What Changes

- Allow an unbound native Guide resource read to enter the same shared request-context bootstrap already used by tools and prompts.
- Return the resulting session ID through the existing resource response contract so later resource reads can resume it with `?session_id=`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mcp-v2-request-context`: Apply the existing opt-in inherited-PWD bootstrap consistently before native resource project checks.
- `mcp-resources-guide-scheme`: Allow an initial eligible native Guide resource read to bootstrap and return its session continuation.

## Impact

- `src/mcp_guide/core/resource_decorator.py`
