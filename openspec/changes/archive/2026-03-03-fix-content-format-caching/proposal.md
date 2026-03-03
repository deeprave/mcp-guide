# Fix Content-Format Flag Not Applied Immediately

## Why

When a user sets the global `content-format` feature flag to `mime`, subsequent content requests do not immediately use MIME formatting. The flag value is correctly persisted to disk and the cache invalidation is called, but the formatter continues to use the default (none) format until an indeterminate time later or after server restart.

This violates the core principle that feature flags are runtime switches that should take effect immediately without requiring server restarts.

## What Changes

- Investigate and fix the caching mechanism for global feature flags in `_ConfigManager`
- Ensure cache invalidation propagates correctly across all session instances
- Add logging to diagnose flag resolution failures hidden by bare exception handlers
- Verify MIME formatter is applied immediately after flag changes

## Impact

- Affected specs: `specs/feature-flags/spec.md`
- Affected code:
  - `src/mcp_guide/session.py` - ConfigManager caching
  - `src/mcp_guide/feature_flags/utils.py` - Flag resolution with bare exception
  - `src/mcp_guide/tools/tool_content.py` - Content formatting
  - `src/mcp_guide/content/formatters/` - Formatter selection
