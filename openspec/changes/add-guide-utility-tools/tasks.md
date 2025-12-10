# Implementation Tasks: Add Guide Utility Tools

**Status:** ✅ COMPLETE - Archived 2025-12-09

**Scope:** Minimal implementation with single utility tool (get_client_info)

**Code Review:** All comments addressed 2025-12-09
- Integration tests made robust (require success, validate schema)
- Caching tests validate actual caching behavior
- Edge case tests cover empty string fallback
- Operator precedence documentation corrected
- AU/UK spelling consistency enforced throughout

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
- [x] 5.1 RED: Write integration test for get_client_info with real session
- [x] 5.2 GREEN: Verify tool returns agent info
- [x] 5.3 RED: Write test for caching across multiple calls
- [x] 5.4 GREEN: Verify agent_info cached on GuideMCP instance
- [x] 5.5 REFACTOR: Clean up test fixtures

## 6. Verification
- [x] 6.1 Run full test suite: `pytest tests/` - All tests passing
- [x] 6.2 Run type checks: `mypy src/` - Success, no issues
- [x] 6.3 Run code quality: `ruff check src/ tests/` - All checks passed
- [x] 6.4 Run formatter: `ruff format src/ tests/` - All files formatted

---

## Test Results

### MCP Test Client Info
The integration tests revealed the MCP test client identifies as:
- **Agent:** mcp
- **Normalized Name:** unknown
- **Version:** 0.1.0
- **Command Prefix:** `/`

### Files Created
1. `src/mcp_guide/guide.py` - GuideMCP class
2. `src/mcp_guide/agent_detection.py` - Agent detection logic
3. `src/mcp_guide/tools/tool_utility.py` - Utility tools
4. `tests/unit/test_guide.py` - GuideMCP tests
5. `tests/unit/test_agent_detection.py` - Agent detection tests
6. `tests/unit/test_mcp_guide/tools/test_tool_utility.py` - Tool tests
7. `tests/integration/test_utility_tools.py` - Integration tests

### Files Modified
1. `src/mcp_guide/server.py` - Use GuideMCP, import tool_utility
2. `src/mcp_guide/tools/tool_constants.py` - Add INSTRUCTION_DISPLAY_ONLY

## Out of Scope (Future Work)
- get_schemas / get_schema (not useful)
- list_prompts (no prompts yet)
- list_resources (needs more thought)
- Template-related functions (separate work item)
- Lifespan support (deferred-tool-registration idea)
