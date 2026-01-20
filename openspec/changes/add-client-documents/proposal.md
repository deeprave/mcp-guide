# Change: Client-Side Document References in Categories

## Why

Categories currently only reference server-side documents. Need ability to reference client-side documents that exist on the agent's filesystem, with session-based caching to avoid repeated requests.

## What Changes

- Extend Category model with `client` dict for client-side document patterns
- Add session-based cache for client documents (positive and negative results)
- Modify `get_category_content` to queue and fetch uncached client documents before delivery
- Add client-side validation against `allowed_read_paths` at category add time and request time
- Support glob patterns in both client pattern and path
- Optional XDG_CACHE persistence for cross-project reuse

## Impact

- Affected specs: `category-tools` (MODIFIED), `content-tools` (MODIFIED), `client-document-cache` (ADDED)
- Dependencies: `filesystem-interaction` (uses `send_file_content`)
- Affected code:
  - `src/mcp_guide/models/category.py` (add client field)
  - `src/mcp_guide/tools/tool_category.py` (validation on add)
  - `src/mcp_guide/tools/tool_content.py` (queue/fetch client docs)
  - `src/mcp_guide/cache/` (new module for document cache)
