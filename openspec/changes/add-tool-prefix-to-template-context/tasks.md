# Implementation Tasks

## Phase 1: Analysis
- [ ] Review current template context building in `src/mcp_guide/utils/template_context_cache.py`
- [ ] Identify where agent_info is populated in the template context
- [ ] Check how MCP_TOOL_PREFIX environment variable is currently used
- [ ] Determine the correct format for the tool_prefix variable (with underscore)

## Phase 2: Implementation
- [ ] Add tool_prefix to agent_info in template context building
- [ ] Read MCP_TOOL_PREFIX from environment variable
- [ ] Apply default "guide_" when MCP_TOOL_PREFIX is not set or is "guide"
- [ ] Append "_" to custom MCP_TOOL_PREFIX values
- [ ] Update template context cache to include tool_prefix

## Phase 3: Testing
- [ ] Test template rendering with default tool prefix ("guide_")
- [ ] Test template rendering with custom MCP_TOOL_PREFIX environment variable
- [ ] Verify tool_prefix appears in agent_info section of template context
- [ ] Test that templates can successfully reference tools using {{tool_prefix}}
- [ ] Test edge cases (empty MCP_TOOL_PREFIX, special characters)

## Phase 4: Documentation
- [ ] Update template documentation to include tool_prefix variable
- [ ] Add examples showing how to use {{tool_prefix}} in templates
- [ ] Document the relationship between MCP_TOOL_PREFIX and tool_prefix

## Phase 5: Check
- [ ] Run existing tests to ensure no regressions
- [ ] Verify backward compatibility with existing templates
- [ ] Manual testing with actual template rendering
- [ ] Test with different MCP_TOOL_PREFIX configurations
