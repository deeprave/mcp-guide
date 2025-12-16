# Change: Add Guide Utility Tools

## Why

Utility tools provide helpful information about the agent/client environment for debugging and context awareness.

## What Changes

- Implement `get_agent_info` tool (returns information about agent/client)
- Return Result pattern responses
- Follow tool conventions (ADR-008)

## Impact

- Affected specs: New capability `guide-utility-tools`
- Affected code: New tools module
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008), category/collection tools
- Breaking changes: None (new tools)
