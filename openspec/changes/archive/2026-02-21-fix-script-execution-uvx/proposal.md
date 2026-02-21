# Change: Fix script execution with uvx

## Why

The `mcp-install` and `guide-agent-install` console scripts fail when executed via `uvx --from mcp-guide` because they import from `scripts` module which is not properly packaged. The scripts are in `src/scripts/` but this directory is not included as a Python package in the distribution.

## What Changes

- Move user-facing script modules from `src/scripts/` to `src/mcp_guide/scripts/`:
  - `mcp_guide_install.py`
  - `guide_agent_install.py`
- Keep `osvcheck.py` in `src/scripts/` (development-only tool)
- Update `pyproject.toml` console script entry points for user scripts to reference `mcp_guide.scripts`
- Update imports in tests for moved scripts

## Impact

- Affected specs: `installation`
- Affected code: `src/scripts/mcp_guide_install.py`, `src/scripts/guide_agent_install.py`, `pyproject.toml`, tests
- **BREAKING**: None - user scripts will work correctly with both `uv run` and `uvx --from mcp-guide`
