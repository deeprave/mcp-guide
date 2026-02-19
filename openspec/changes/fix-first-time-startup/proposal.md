# Change: Fix First-Time Startup Initialization

## Why

When guide is installed as an MCP server and `~/.config/mcp-guide` does not exist, first-time startup fails because `lock_update()` cannot create lock files when the parent directory doesn't exist.

The existing initialization mechanism in `Session._ConfigManager.get_or_create_config()` is designed to install templates and create config on first run, but it never gets called because `lock_update()` fails first with `FileNotFoundError` when trying to create the lock file.

## What Changes

Modify `lock_update()` in `file_lock.py` to handle missing parent directory:

1. Create `ConfigDirectoryError` exception class
2. Catch `FileNotFoundError` when creating lock file
3. Check if parent directory exists
4. If not, create it (log and raise ConfigDirectoryError on failure)
5. Retry lock creation (log and raise ConfigDirectoryError on failure)
6. Add exception handler in main entry point to catch ConfigDirectoryError and exit with code 2

Both failure scenarios are fatal - if we can't materialize our config, the MCP server cannot continue. The exception propagates to main which exits with a specific error code (2) indicating conditions to run MCP cannot be met.

## Impact

- Affected specs: `mcp-server`
- Affected code: `src/mcp_guide/file_lock.py`
- Breaking: None - only fixes broken first-time startup
- Benefits: Automatic initialization works as designed, clear error logging on fatal failures
