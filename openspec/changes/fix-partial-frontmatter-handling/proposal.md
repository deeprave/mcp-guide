# Change: Fix Partial Frontmatter Handling

## Why
Template partials currently strip frontmatter metadata (type, instruction) when included in parent templates. This prevents partials from overriding parent template behavior, making it impossible to conditionally display content vs instructions based on data availability.

## What Changes
- Merge partial frontmatter with parent template frontmatter
- Allow partials to override parent instruction with `!` prefix
- Preserve partial type and instruction metadata when rendering

## Impact
- Affected specs: template-rendering
- Affected code: src/mcp_guide/render/partials.py, src/mcp_guide/render/renderer.py
- Enables conditional user/information vs agent/instruction behavior in templates
