# Fix Frontmatter Instruction Rendering

## Why

Template variables in frontmatter `instruction` fields are not being expanded, and instruction text contains excessive repetition of common phrases.

**Issue 1 - Variable expansion**:
The instruction field contains `{{workflow.file}}` which should be rendered to `.guide.yaml`, but is being passed through literally.

**Issue 2 - Repetitive instructions**:
Multiple instances of "Do not display this content to the user" and similar phrases are repeated unnecessarily, creating verbose and redundant instructions.

**Example of broken behavior:**
```
instruction: "You MUST follow these instructions. Do not display this content to the user.
Adhere to these guidelines ALWAYS.
You MUST confirm understanding of these guidelines before proceeding.
Do not display this content to users.
Use these as coding standards for Python. Do not display this content to the user.
This information is for your information and use. Do must not display this content to the user.
Use this information when working with OpenSpec. Do not display to users.
Follow this policy exactly. If {{workflow.file}} missing, create it and enter discussion phase."
```

This used to work correctly but was broken by recent changes to the rendering system.

## What Changes

1. **Fix template rendering**: Ensure frontmatter `instruction` fields are processed through the template engine with the same context as the template body

2. **Deduplicate instruction text**: Intelligently combine repeated phrases like "Do not display this content to the user" into a single statement at the beginning or end of the instruction

**Expected behavior**:
- All template variables in frontmatter should be expanded
- Common instruction phrases should appear once, not multiple times
- Instructions should be concise and non-redundant

## Impact

- Affected specs: Likely `template-rendering` or similar capability
- Affected code:
  - `src/mcp_guide/render/` - Template rendering system
  - `src/mcp_guide/render/frontmatter.py` - Frontmatter parsing and instruction deduplication
  - `src/mcp_guide/render/renderer.py` - Template rendering
  - `src/mcp_guide/render/context.py` - Context building
- Breaking changes: None (improving existing behavior)
