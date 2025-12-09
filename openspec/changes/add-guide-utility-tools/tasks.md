# Implementation Tasks: Add Guide Utility Tools

**Status:** ✅ IMPLEMENTATION COMPLETE - Ready for CHECK phase

**Scope:** Minimal implementation with single utility tool (get_client_info)

## 1. Create GuideMCP Class
- [x] 1.1 RED: Write test for GuideMCP initialization
- [x] 1.2 GREEN: Create `src/mcp_guide/guide.py` with GuideMCP class extending FastMCP
- [x] 1.3 GREEN: Add `agent_info: Optional[AgentInfo] = None` attribute
- [x] 1.4 REFACTOR: Verify type hints and docstring

## 2. Implement Agent Detection
- [x] 2.1 RED: Write test for AgentInfo dataclass
- [x] 2.2 GREEN: Create `src/mcp_guide/agent_detection.py` with AgentInfo
- [x] 2.3 RED: Write test for normalize_agent_name()
- [x] 2.4 GREEN: Implement normalize_agent_name() with AGENT_PATTERNS
- [x] 2.5 RED: Write test for detect_agent() with various client_params
- [x] 2.6 GREEN: Implement detect_agent() with AGENT_PREFIX_MAP
- [x] 2.7 RED: Write test for format_agent_info()
- [x] 2.8 GREEN: Implement format_agent_info()
- [x] 2.9 REFACTOR: Clean up constants and error handling

## 3. Implement get_client_info Tool
- [x] 3.1 RED: Write test for get_client_info with no cache
- [x] 3.2 GREEN: Add INSTRUCTION_DISPLAY_ONLY to tool_constants.py
- [x] 3.3 GREEN: Create `src/mcp_guide/tools/tool_utility.py` with get_client_info
- [x] 3.4 RED: Write test for get_client_info with cached agent_info
- [x] 3.5 GREEN: Implement caching logic
- [x] 3.6 RED: Write test for missing client_params error
- [x] 3.7 GREEN: Add error handling
- [x] 3.8 REFACTOR: Clean up formatting and error messages

## 4. Update Server
- [x] 4.1 Update `server.py` to import GuideMCP instead of FastMCP
- [x] 4.2 Update `server.py` to import tool_utility module
- [x] 4.3 Verify server starts and tool is registered

## 5. Integration Tests
- [ ] 5.1 RED: Write integration test for get_client_info with real session
- [ ] 5.2 GREEN: Verify tool returns agent info
- [ ] 5.3 RED: Write test for caching across multiple calls
- [ ] 5.4 GREEN: Verify agent_info cached on GuideMCP instance
- [ ] 5.5 REFACTOR: Clean up test fixtures

## 6. Verification
- [x] 6.1 Run full test suite: `pytest tests/` - 664 tests passed (663 passed, 1 skipped)
- [x] 6.2 Run type checks: `mypy src/` - Success, no issues
- [x] 6.3 Run code quality: `ruff check src/ tests/` - All checks passed
- [x] 6.4 Run formatter: `ruff format src/ tests/` - 5 files reformatted

---

## Architecture

### GuideMCP Class
```python
# src/mcp_guide/guide.py
from typing import Optional
from fastmcp import FastMCP
from mcp_guide.agent_detection import AgentInfo

class GuideMCP(FastMCP):
    """Extended FastMCP with agent info caching."""

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.agent_info: Optional[AgentInfo] = None
```

### Agent Detection
```python
# src/mcp_guide/agent_detection.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentInfo:
    name: str
    normalized_name: str
    version: Optional[str]
    prompt_prefix: str

AGENT_PREFIX_MAP = {
    "kiro": "@",
    "claude": "/{mcp_name}:",
    "copilot": "/",
}

AGENT_PATTERNS = [
    (r"kiro", "kiro"),
    (r"claude", "claude"),
    (r"copilot", "copilot"),
]

def normalize_agent_name(name: str) -> str:
    """Normalize agent name to lowercase canonical form."""

def detect_agent(client_params: dict) -> AgentInfo:
    """Detect agent from client parameters."""

def format_agent_info(agent_info: AgentInfo, mcp_name: str) -> str:
    """Format agent info for display."""
```

### Tool Implementation
```python
# src/mcp_guide/tools/tool_utility.py
from mcp_guide.tools import tools
from mcp_guide.result import Result
from mcp_guide.tools.tool_constants import INSTRUCTION_DISPLAY_ONLY

@tools.tool()
async def get_client_info(ctx: Context) -> str:
    """Get information about the MCP client/agent.

    Returns cached agent info if available, otherwise detects
    and caches for future calls.
    """
    # Check cache
    if ctx.fastmcp.agent_info:
        agent_info = ctx.fastmcp.agent_info
    else:
        # Detect and cache
        if not ctx.session.client_params:
            return Result.error("No client information available").to_json_str()

        agent_info = detect_agent(ctx.session.client_params)
        ctx.fastmcp.agent_info = agent_info

    # Format and return
    formatted = format_agent_info(agent_info, ctx.fastmcp.name)
    result = Result.ok(formatted)
    result.instruction = INSTRUCTION_DISPLAY_ONLY
    return result.to_json_str()
```

## Files to Create
1. `src/mcp_guide/guide.py` - GuideMCP class
2. `src/mcp_guide/agent_detection.py` - Agent detection logic
3. `src/mcp_guide/tools/tool_utility.py` - Utility tools
4. `tests/unit/test_guide.py` - GuideMCP tests
5. `tests/unit/test_agent_detection.py` - Agent detection tests
6. `tests/unit/test_mcp_guide/tools/test_tool_utility.py` - Tool tests
7. `tests/integration/test_utility_tools.py` - Integration tests

## Files to Modify
1. `src/mcp_guide/server.py` - Use GuideMCP, import tool_utility
2. `src/mcp_guide/tools/tool_constants.py` - Add INSTRUCTION_DISPLAY_ONLY

## Out of Scope (Future Work)
- get_schemas / get_schema (not useful)
- list_prompts (no prompts yet)
- list_resources (needs more thought)
- Template-related functions (separate work item)
- Lifespan support (deferred-tool-registration idea)

## Architecture

### GuideMCP Class (Simplified)
```python
# src/mcp_guide/guide.py
class GuideMCP(FastMCP):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.agent_info: Optional[AgentInfo] = None
```

### Agent Detection
```python
# src/mcp_guide/agent_detection.py
@dataclass
class AgentInfo:
    name: str
    normalized_name: str
    version: Optional[str]
    prompt_prefix: str

AGENT_PREFIX_MAP = {
    "kiro": "@",
    "claude": "/{mcp_name}:",
    "copilot": "/",
    # ...
}
```

### Tool Implementation
```python
# src/mcp_guide/tools/tool_utility.py
@tools.tool()
async def get_client_info(ctx: Context) -> str:
    # Check cache
    if ctx.fastmcp.agent_info:
        return format_cached()

    # Detect and cache
    agent_info = detect_agent(ctx.session.client_params)
    ctx.fastmcp.agent_info = agent_info

    # Return formatted result
    result = Result.ok(format_agent_info(...))
    result.instruction = INSTRUCTION_DISPLAY_ONLY
    return result.to_json_str()
```

## Files to Create
1. `src/mcp_guide/guide.py`
2. `src/mcp_guide/agent_detection.py`
3. `src/mcp_guide/tools/tool_utility.py`
4. `tests/unit/test_agent_detection.py`
5. `tests/unit/test_mcp_guide/tools/test_tool_utility.py`
6. `tests/integration/test_utility_tools.py`

## Files to Modify
1. `src/mcp_guide/server.py` - Use GuideMCP, import tool_utility
2. `src/mcp_guide/tools/tool_constants.py` - Add INSTRUCTION_DISPLAY_ONLY

## Estimated Effort
~3 hours total (TDD approach with smallest possible steps)

