# Implementation Plan: Fix Scripts with uvx

## Problem
The `guide-agent-install` script returns an empty list when run via `uvx --from mcp-guide guide-agent-install -l` or direct execution. The script cannot find agent configuration files.

## Root Cause
Path resolution bug in `src/mcp_guide/scripts/guide_agent_install.py`:

```python
agents_base = Path(__file__).parent.parent / "mcp_guide" / "agents"
```

This resolves to `src/mcp_guide/mcp_guide/agents` (incorrect) instead of `src/mcp_guide/agents` (correct).

## Solution
Fix path resolution to correctly locate the agents directory relative to the installed package, not the script file location.

## Tasks

### 1. Fix Path Resolution
- [x] 1.1 Update `get_available_agents()` in `guide_agent_install.py`
  - Use `importlib.resources` or package-relative path
  - Change from `Path(__file__).parent.parent / "mcp_guide" / "agents"` 
  - To: `Path(__file__).parent.parent / "agents"` (simplest fix)
- [x] 1.2 Update `main()` function's `agents_base` variable with same fix
- [x] 1.3 Verify agents directory structure is correct

### 2. Test Fix
- [x] 2.1 Test direct execution: `guide-agent-install -l`
- [x] 2.2 Test uvx execution: `uvx --from mcp-guide guide-agent-install -l`
- [x] 2.3 Test agent installation: `guide-agent-install kiro ~/test-dir`
- [x] 2.4 Verify all agent configs are found (kiro, etc.)

### 3. Check mcp-install Script
- [x] 3.1 Review `mcp_guide_install.py` for similar path issues
- [x] 3.2 Test if affected: `uvx --from mcp-guide mcp-install --help`
- [x] 3.3 Fix if needed

### 4. Documentation
- [x] 4.1 Update CHANGELOG.md with bug fix
- [x] 4.2 No user docs needed (internal bug fix)

## Implementation Notes

**Simplest Fix:**
```python
# Line 12 in guide_agent_install.py
agents_base = Path(__file__).parent.parent / "agents"  # Remove "mcp_guide" segment

# Line 29 in main()
agents_base = Path(__file__).parent.parent / "agents"  # Same fix
```

**Why This Works:**
- `Path(__file__)` = `src/mcp_guide/scripts/guide_agent_install.py`
- `.parent` = `src/mcp_guide/scripts/`
- `.parent.parent` = `src/mcp_guide/`
- `/ "agents"` = `src/mcp_guide/agents/` ✓

## Verification
After fix, `guide-agent-install -l` should output:
```
Available agents:
  - kiro
```
