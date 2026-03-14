# Change: Unify Rendering Pipelines

## Why
Frontmatter processing and file rendering logic is duplicated across 4 locations (render/template.py, render/partials.py, discovery/commands.py, content/utils.py). This creates maintenance burden, inconsistency risk, and makes changes difficult to propagate.

## What Changes
Progressive refactor in two phases:

**Phase 1: Unify Frontmatter Processing**
- Create `process_frontmatter()` - combines parse + requirements check + instruction/description rendering
- Replace 4 duplicate implementations with single function
- ~80-100 lines of duplication removed

**Phase 2: Unify File Processing**
- Create `process_file()` - single entry point for template and non-template files
- Eliminate template vs non-template branching duplication
- Remove inline frontmatter parsing from command discovery
- ~100-150 lines of duplication removed

## Impact
- Affected specs: frontmatter-processing, template-rendering, command-discovery, content-retrieval
- Affected code:
  - `src/mcp_guide/render/frontmatter.py` (new functions)
  - `src/mcp_guide/render/template.py` (use new functions)
  - `src/mcp_guide/render/partials.py` (use new functions)
  - `src/mcp_guide/render/renderer.py` (use new functions)
  - `src/mcp_guide/discovery/commands.py` (remove inline parsing)
  - `src/mcp_guide/content/utils.py` (use new functions)
- Breaking changes: None (internal refactor only)
