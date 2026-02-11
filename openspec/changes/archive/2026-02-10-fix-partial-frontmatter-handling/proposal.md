# Change: Fix Partial Frontmatter Handling

## Why
Template partials currently strip frontmatter metadata (type, instruction) when included in parent templates. This prevents partials from overriding parent template behavior, making it impossible to conditionally display content vs instructions based on data availability.

Instruction resolution logic is duplicated across:
- Single template rendering (`render/content.py`)
- Multiple content aggregation (`content/utils.py`)
- Partial rendering lacks this entirely

## What Changes
- Create centralized instruction resolution function supporting:
  - `!` prefix for important instructions that override regular ones
  - Type-based default fallback
  - Deduplication logic
- Merge partial frontmatter with parent template frontmatter
- Apply instruction resolution to partials using shared function
- Preserve partial type and instruction metadata when rendering

## Impact
- Affected specs: template-rendering
- Affected code:
  - src/mcp_guide/render/frontmatter.py (new shared function)
  - src/mcp_guide/render/partials.py (merge frontmatter, use shared resolver)
  - src/mcp_guide/render/content.py (use shared resolver)
  - src/mcp_guide/content/utils.py (use shared resolver)
- Enables conditional user/information vs agent/instruction behavior in templates
- Centralizes instruction resolution logic for consistency
