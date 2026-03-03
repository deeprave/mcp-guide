# Change: Fix Scripts with uvx

## Why
The `guide-agent-install` and potentially `mcp-install` scripts are not working correctly when run via `uvx --from mcp-guide`. The agent configuration is not being found, resulting in empty output.

## What Changes

### Investigation Required
- Determine why `guide-agent-install -l` returns empty list when run via uvx
- Check if `mcp-install` is similarly affected
- Identify root cause (package data, entry points, path resolution, etc.)

### Fix Implementation
- Ensure agent configuration files are properly included in package
- Verify entry point configuration in `pyproject.toml`
- Fix path resolution if needed
- Ensure scripts work consistently via:
  - Direct execution: `guide-agent-install -l`
  - uvx execution: `uvx --from mcp-guide guide-agent-install -l`
  - pip install execution: `pip install mcp-guide && guide-agent-install -l`

## Impact
- **Affected specs**: packaging, scripts
- **Affected code**:
  - `pyproject.toml` - Entry points, package data
  - `src/mcp_guide/scripts/` - Script implementations
  - `MANIFEST.in` or package configuration - Data file inclusion
- **Benefits**:
  - Consistent script behavior across installation methods
  - Reliable agent installation workflow
  - Better user experience
