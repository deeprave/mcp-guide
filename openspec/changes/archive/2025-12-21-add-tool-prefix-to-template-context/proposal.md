# Add Tool Prefix to Template Context

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

The MCP tool prefix is configurable via the `MCP_TOOL_PREFIX` environment variable, but this information is not available in template contexts. This creates a problem when templates need to reference specific MCP tools by name, as they cannot dynamically construct the correct tool names.

Currently, templates that want to reference tools must hardcode the prefix (e.g., "guide_get_content"), but this breaks when users configure a different tool prefix. This makes templates less portable and creates maintenance issues.

The tool prefix should be available in the template context alongside other agent information like the prompt character (`{{@}}`), allowing templates to dynamically construct correct tool references.

## What Changes

- Add `tool_prefix` variable to the agent_info section of template context
- The variable should include the underscore separator (e.g., "guide_" not "guide")
- Default value should be "guide_" when MCP_TOOL_PREFIX is not set or is "guide"
- When MCP_TOOL_PREFIX is set to a custom value, append "_" to create the prefix
- Update template context building to read MCP_TOOL_PREFIX from environment

## Technical Approach

The tool prefix should be determined from the MCP_TOOL_PREFIX environment variable and made available in templates as `{{tool_prefix}}`. This allows templates to reference tools like `{{tool_prefix}}get_content` which would resolve to `guide_get_content` by default.

## Success Criteria

- Templates can use `{{tool_prefix}}` to dynamically reference MCP tools
- The prefix correctly reflects the MCP_TOOL_PREFIX environment variable
- Default behavior maintains "guide_" prefix for backward compatibility
- Custom tool prefixes work correctly in templates
