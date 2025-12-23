# Change: Add Config File Watcher

## Why
The system needs to automatically detect configuration file changes and notify active sessions to reload their configuration without requiring manual restarts or polling.

## What Changes
- Add PathWatcher generic file monitoring capability in mcp_core
- Add WatcherRegistry for managing watcher instances
- Add ConfigWatcher for config-specific file monitoring with caching
- Integrate with session management for automatic notifications

## Impact
- Affected specs: config-management
- Affected code: src/mcp_core/path_watcher.py, src/mcp_core/watcher_registry.py, src/mcp_guide/watchers/config_watcher.py
- New capability: Real-time config change detection and session notification
