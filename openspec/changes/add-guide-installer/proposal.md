# Change: Guide Installer

## Why

New installations require manual setup of docroot and configuration. Need automated installation that:
- Runs automatically on first startup when config doesn't exist
- Provides manual script for updates
- Shares code between automatic and manual installation
- Follows async-first pattern from mcp-server-guide

## What Changes

Add installation system with shared async implementation:
- Automatic installation on first startup (no config file)
- Manual installer script at `src/scripts/mcp_guide_install.py`
- Non-interactive by default, -i/--interactive for prompts
- CLI options: -d/--docroot, -c/--configdir (script and server)
- Shared installer module with core logic
- Templates from mcp_guide_templates package
- Smart update strategy:
  - Track original files in `_installed.zip` in docroot
  - Skip files identical to new version (SHA256)
  - Update unchanged files without backup
  - Apply user diffs to new version when possible
  - Backup and warn when diff fails
- Path validation for security

## Impact

- Affected specs: `installation` (ADDED), `mcp-server` (MODIFIED)
- Affected code:
  - `src/mcp_guide/installer/` (new module for shared logic)
  - `src/scripts/mcp_guide_install.py` (new CLI script)
  - `src/mcp_guide/server.py` (check config on startup, add -d/-c options)
  - `pyproject.toml` (add mcp-install console script, mcp_guide_templates package)
  - `templates/` directory packaged as mcp_guide_templates
