# Change: Unify Template Rendering

## Why
Template rendering is currently fragmented across the codebase with inconsistent handling of frontmatter rules and special template types. Different rendering paths exist for commands, workflow, openspec, and common templates, leading to duplication and inconsistent behavior.

## What Changes
- Create unified template rendering system with consistent frontmatter parsing
- Standardise handling of special template types (commands, workflow, openspec, common)
- Consolidate rendering logic into single coherent system
- Apply frontmatter rules uniformly across all template types

## Impact
- Affected specs: template-system, template-support, workflow-templates
- Affected code:
  - `src/mcp_guide/utils/template_renderer.py`
  - `src/mcp_guide/workflow/rendering.py`
  - Template rendering call sites throughout codebase
