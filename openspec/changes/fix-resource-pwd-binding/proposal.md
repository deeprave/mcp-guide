# Proposal

## Why

An opted-in stdio client with a verified shared inherited `PWD` can bootstrap a project through tools and prompts, but its first native `resources/read` request is rejected before the shared bootstrap runs. This prevents agents that begin with `guide://_status` from using the intended PWD shortcut.

## What Changes

- Allow an eligible first native Guide resource request to enter the shared request-context bootstrap without weakening the explicit resource-session requirement.
- Ensure underscore-prefixed command URIs reach the dedicated command resource template instead of a generic content template.
- Return the resulting session ID through the existing resource response contract so later resource reads can resume it with `?session_id=`.
- Add one native-resource regression test for the first PWD-bootstrapped request and its returned session ID.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mcp-v2-request-context`: Apply the existing opt-in inherited-PWD bootstrap consistently before native resource project checks.
- `mcp-resources-guide-scheme`: Allow an initial eligible native Guide resource read to bootstrap and return its session continuation.

## Impact

- `src/mcp_guide/core/resource_decorator.py`
- `src/mcp_guide/resources.py`
- Native resource integration coverage
