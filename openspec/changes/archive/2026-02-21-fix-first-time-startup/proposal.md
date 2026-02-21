# Change: Fix First-Time Startup Initialization

## Why

When guide is installed as an MCP server and `~/.config/mcp-guide` does not exist, first-time startup fails because `lock_update()` cannot create lock files when the parent directory doesn't exist.

The existing initialization mechanism in `Session._ConfigManager.get_or_create_config()` is designed to install templates and create config on first run, but it never gets called because `lock_update()` fails first with `FileNotFoundError` when trying to create the lock file.

## What Changes

Add a helper method in `Session._ConfigManager` to ensure the config directory exists before reading/saving config:

1. Add `_ensure_config_dir()` method to `_ConfigManager` class
2. Method checks if `self.config_file.parent` exists
3. If not, calls `makedirs(exist_ok=True)` to create it
4. Logs any exception during directory creation and continues
5. Call `_ensure_config_dir()` only in methods that read/save the config file itself (not flags or other operations)

This is a minimal fix confined to `_ConfigManager` that ensures the directory exists before the first config file access.

## Impact

- Affected specs: `mcp-server`
- Affected code: `src/mcp_guide/file_lock.py`
- Breaking: None - only fixes broken first-time startup
- Benefits: Automatic initialization works as designed, clear error logging on fatal failures
