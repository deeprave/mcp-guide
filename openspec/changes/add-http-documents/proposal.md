# Change: HTTPS Document References in Categories

## Why

Categories currently only reference server-side documents. Need ability to reference remote HTTPS documents with security controls (allowlist/blocklist) and session-based caching.

## What Changes

- Extend Category model with `https` dict for HTTPS document patterns
- Add server-side HTTPS fetching with retry logic for temporary failures
- Add allowlist/blocklist security configuration (global and per-project)
- Add session-based cache for HTTPS documents (positive and negative results)
- Modify `get_category_content` to queue and fetch uncached HTTPS documents before delivery
- Enforce HTTPS-only (no HTTP support)

## Impact

- Affected specs: `category-tools` (MODIFIED), `content-tools` (MODIFIED), `document-cache` (ADDED), `https-document-security` (ADDED)
- Affected code:
  - `src/mcp_guide/models/category.py` (add https field)
  - `src/mcp_guide/tools/tool_category.py` (validation on add)
  - `src/mcp_guide/tools/tool_content.py` (queue/fetch HTTPS docs)
  - `src/mcp_guide/cache/` (new module for document cache)
  - `src/mcp_guide/security/https_policy.py` (new module for allowlist/blocklist)
  - Configuration files (global and project-level security settings)

**Note:** This change shares cache infrastructure with `add-client-documents`. Whichever is implemented first creates the cache mechanism.
