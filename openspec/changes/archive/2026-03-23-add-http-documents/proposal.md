# Change: URL Document References in Categories

## Why

Categories currently only reference local server-side documents. Projects need the ability to include content from remote URLs as category documents. The agent fetches and converts content to markdown at category add time, and the MCP caches it persistently for fast retrieval. A background task monitors source URLs for changes using HTTP headers and flags stale documents for refresh.

## What Changes

- Extend Category model with `urls` dict mapping patterns to URL references (with per-document refresh interval, default 7 days)
- All pattern-modifying tools (`category_add`, `category_change`, `category_update`, and collection equivalents) accept URL parameters
- At add time: MCP instructs agent to fetch URL → agent converts to markdown → agent sends back via `send_file_content` with interceptable format → MCP caches persistently
- If fetch fails at add time, the URL/pattern is not added
- Persistent cache in single-file compact format (SQLite) in XDG cache directory with full metadata
- Background "document handler" task checks `Last-Modified` / `ETag` headers when refresh interval expires — marks documents stale only, does not re-fetch
- Stale documents continue to be served; staleness is flagged in listing tools
- `get_category_content`, `get_content`, `export_content` serve cached URL content alongside local files
- A refresh tool allows the agent to re-fetch stale documents
- Protocol-agnostic: HTTP and HTTPS URLs accepted, agent security is relied upon

## Impact

- Affected specs: `category-tools` (MODIFIED), `content-tools` (MODIFIED), `models` (MODIFIED), `document-cache` (ADDED), `document-handler-task` (ADDED)
- Affected code:
  - Category model (add urls field)
  - All category/collection tools that modify patterns (add URL handling)
  - Content delivery pipeline (include cached documents)
  - New persistent document cache module
  - New document handler background task
  - `send_file_content` interception for URL document format
- **Prerequisite:** `refactor-session-project` should be completed first to clean up session/project separation

**Note:** This change shares cache infrastructure with `add-client-documents`. Whichever is implemented first creates the cache mechanism.
