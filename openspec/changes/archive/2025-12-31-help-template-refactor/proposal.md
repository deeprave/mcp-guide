# Change: Help Template Refactor

## Why
The current help system generates help content programmatically as strings in `get_command_help()`. This approach limits flexibility for upcoming workflow management features that may need richer help formatting, conditional content, and integration with template-based styling systems.

## What Changes
- Refactor help system to use template-based rendering instead of programmatic string generation
- Update `get_command_help()` to populate template context with command metadata
- Create help template that can render individual command help with full template capabilities
- Enable workflow-aware help content through template conditionals
- Maintain backward compatibility with existing help functionality

## Impact
- Affected specs: New `help-template-system` capability
- Affected code:
  - `src/mcp_guide/prompts/guide_prompt.py` - Refactor `get_command_help()`
  - `templates/_commands/help.mustache` - Enhanced help template
  - Template context system - Add command help context support
