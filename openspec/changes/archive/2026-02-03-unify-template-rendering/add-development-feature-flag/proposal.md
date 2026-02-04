# Proposal: Add Development Feature Flag

## Problem Statement

Command discovery currently checks filesystem mtimes on every execution to detect changes, even in production environments where commands are static. This adds unnecessary overhead for a use case (detecting command changes during development) that doesn't apply in production.

## Proposed Solution

Add a `guide-development` feature flag that controls whether command discovery performs mtime checks:

- **When enabled (development):** Check mtimes on every call to detect command changes
- **When disabled (production):** Trust the cache indefinitely after first scan

## Benefits

1. **Performance:** Eliminates directory traversal overhead in production
2. **Clarity:** Explicit flag for development vs production behavior
3. **Flexibility:** Users can enable during development, disable in production

## Implementation Approach

1. Add `guide-development` boolean feature flag
2. Update `discover_commands()` to check flag before mtime validation
3. When flag is false/unset, use cached commands without mtime check
4. Add validator to ensure flag is boolean only

## Scope

- Feature flag definition and validation
- Command discovery cache behavior
- Documentation

## Non-Goals

- Automatic detection of development environment
- File watching or hot reload
- Other caching optimizations
