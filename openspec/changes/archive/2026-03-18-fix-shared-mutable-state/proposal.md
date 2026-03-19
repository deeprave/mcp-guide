# Change: Fix Shared Mutable State for HTTP Multi-Client Isolation

## Why

Three module-level mutable caches are shared across all async tasks. In HTTP transport
with concurrent clients, this causes cross-client contamination:

1. `_command_cache` — caches discovered commands keyed by directory path, but the cached
   result includes `requires-*` frontmatter filtering based on the requesting session's
   flags. Client B may receive commands filtered for Client A's context.
2. `_file_cache` — module-level `FileCache()` singleton caches file content sent by agents.
   One client's file submissions are visible to another.
3. `TaskManager._instance` — singleton shared across all clients. Instruction queue,
   timer tasks, and event dispatch are not isolated per-client.

## What Changes

- Move `_command_cache` into `Session` — session is already task-local via ContextVar,
  so the cache becomes naturally isolated. No new dependencies.
- Convert `_file_cache` to a `ContextVar[FileCache]` — keeps it isolated per-task without
  adding a dependency on Session. Avoids circular imports.
- Convert `TaskManager` to per-task via `ContextVar` — each client gets its own manager,
  own tasks, and private event dispatch. Created on demand.

## Impact

- Affected specs: `session-management` (MODIFIED)
- Affected code:
  - `src/mcp_guide/discovery/commands.py` — move `_command_cache` to session
  - `src/mcp_guide/filesystem/tools.py` — `_file_cache` becomes ContextVar
  - `src/mcp_guide/filesystem/cache.py` — no changes (FileCache class unchanged)
  - `src/mcp_guide/task_manager/manager.py` — singleton → ContextVar
- **BREAKING**: None externally. Internal change only.
