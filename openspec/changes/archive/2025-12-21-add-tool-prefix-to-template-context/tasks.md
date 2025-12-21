# Implementation Tasks

## Phase 1: Analysis
- [x] Review current template context building in `src/mcp_guide/utils/template_context_cache.py`
- [x] Identify where agent_info is populated in the template context
- [x] Check how MCP_TOOL_PREFIX environment variable is currently used
- [x] Determine the correct format for the tool_prefix variable (with underscore)

## Phase 2: Implementation
- [x] Add tool_prefix to agent_info in template context building
- [x] Read MCP_TOOL_PREFIX from environment variable
- [x] Apply default "guide_" when MCP_TOOL_PREFIX is not set or is "guide"
- [x] Append "_" to custom MCP_TOOL_PREFIX values
- [x] Update template context cache to include tool_prefix

## Phase 3: Testing
- [x] Test template rendering with default tool prefix ("guide_")
- [x] Test template rendering with custom MCP_TOOL_PREFIX environment variable
- [x] Verify tool_prefix appears in agent_info section of template context
- [x] Test that templates can successfully reference tools using {{tool_prefix}}
- [x] Test edge cases (empty MCP_TOOL_PREFIX, special characters)

## Phase 4: Documentation
- [x] Update template documentation to include tool_prefix variable
- [x] Add examples showing how to use {{tool_prefix}} in templates
- [x] Document the relationship between MCP_TOOL_PREFIX and tool_prefix

## Phase 5: Check
- [x] Run existing tests to ensure no regressions
- [x] Verify backward compatibility with existing templates
- [x] Manual testing with actual template rendering
- [x] Test with different MCP_TOOL_PREFIX configurations
