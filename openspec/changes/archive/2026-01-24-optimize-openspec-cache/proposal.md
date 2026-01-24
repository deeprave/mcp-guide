# Optimize OpenSpec Integration with Caching

## Overview

Eliminate redundant directory scanning and cache `openspec list --json` output in template context for efficient access to OpenSpec changes data.

## Problem

Current implementation wastes time and tokens:
- Unnecessary directory listings for `openspec/` and `openspec/changes/`
- No caching of `openspec list --json` output
- Agent re-runs `openspec list` every time it needs change information
- Multiple tools query the same data repeatedly

## Solution

Cache `openspec list --json` output in template context with:
- 15-minute TTL to prevent stale data
- Event-based invalidation when changes are created/modified
- Single source of truth for all OpenSpec commands
- Remove directory scanning from prompts

## Impact

- Eliminates 2 unnecessary directory scans per session
- Reduces latency for `:openspec/list` and `:openspec/status` commands
- Reduces token usage significantly
- Improves user experience with faster responses
- No breaking changes to command interface

## Related

- Template context system (already implemented)
- OpenSpec CLI integration (already implemented)
- File watching system (for cache invalidation)
