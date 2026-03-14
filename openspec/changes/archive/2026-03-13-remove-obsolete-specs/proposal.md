# Change: Remove obsolete specs and stale requirements

## Why
Several specs describe systems that were never built or have since been replaced, and two specs contain requirements for tools that were removed in `consolidate-tools`. These create misleading documentation and spec drift.

## What Changes
- **Remove `workflow-fsm` spec** — FSM was never implemented; the actual system is the pubsub/event model documented in `workflow-events`
- **Rename `refactor-task-pubsub` spec to `workflow-events`** — name reflects what the spec actually describes
- **Remove `test-isolation` spec** — reads as a planning/implementation notes document, not a spec; the isolation is already implemented in `tests/conftest.py`
- **Remove `mcp-discovery` spec** — `list_tools`, `list_prompts`, `list_resources` were unregistered as MCP tools in `consolidate-tools`; functions are retained internally but are no longer exposed tools
- **Remove `get_flag Tool` requirement from `mcp-server` spec** — `get_flag` was removed in `consolidate-tools`; functionality merged into `list_*_flags` with `feature_name` parameter

No cross-references to these specs or requirements exist in other specs.

## Impact
- Affected specs: `workflow-fsm` (deleted), `test-isolation` (deleted), `mcp-discovery` (deleted), `mcp-server` (modified), `refactor-task-pubsub` (renamed to `workflow-events`)
- No code changes required
