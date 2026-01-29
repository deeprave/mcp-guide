# Template Rendering System Design

## Overview

A template rendering system that accepts template names or patterns, discovers files, parses frontmatter, and renders templates with consistent context handling. The system separates rendering concerns from output handling, allowing callers to decide what to do with rendered content.

## Core Principles

1. **Single Responsibility**: Each component does one thing well
2. **Separation of Concerns**: Discovery → Parsing → Rendering → Output (caller's responsibility)
3. **Consistency**: Same frontmatter rules, same context handling, same rendering path
4. **Minimal**: YAGNI - only what's needed, no speculative features
5. **Caller Control**: System renders, caller decides what to do with output
6. **Type Safety**: Frontmatter uses typed accessors to prevent type errors

## Architecture

### Component Layers

```
┌─────────────────────────────────────────────────────────┐
│ Caller (tools, prompts, tasks)                          │
│ - Builds context                                         │
│ - Calls renderer                                         │
│ - Handles rendered output                                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Template Renderer                                        │
│ - Discovers templates                                    │
│ - Parses frontmatter (returns Frontmatter)               │
│ - Checks requirements                                    │
│ - Renders templates                                      │
│ - Returns RenderedContent                                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Core Components (existing)                               │
│ - discover_category_files()                              │
│ - parse_content_with_frontmatter()                       │
│ - Frontmatter (type-safe dict)                           │
│ - check_frontmatter_requirements()                       │
│ - render_template_content()                              │
└─────────────────────────────────────────────────────────┘
```

## Type-Safe Frontmatter

### Frontmatter Class

```python
class Frontmatter(dict):
    """Type-safe frontmatter dictionary with typed accessors."""

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get string value, converting to lowercase if present."""

    def get_list(self, key: str, default: Optional[List[str]] = None) -> Optional[List[str]]:
        """Get list value, wrapping single values in a list."""

    def get_dict(self, key: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get dict value."""

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get boolean value."""
```

**Benefits:**
- Type safety at access time
- Automatic lowercase conversion for strings
- Single value → list wrapping
- Clear error messages for type mismatches
- Centralised frontmatter handling logic

## API Design

### Primary Interface

```python
async def render_template(
    file_info: FileInfo,
    base_dir: Path,
    project_flags: Dict[str, Any],
    context: Optional[TemplateContext] = None,
    docroot: Optional[Path] = None,
) -> Optional[RenderedContent]:
    """
    Render a template with consistent frontmatter and context handling.

    Args:
        file_info: FileInfo object from discovery
        base_dir: Base directory for resolving paths
        project_flags: Resolved project flags for requires-* checking
        context: Optional local context from caller
        docroot: Document root for security validation

    Returns:
        RenderedContent if requirements met, None if filtered out

    Process:
        1. Load content and parse frontmatter
        2. Check requires-* against project_flags (return None if flag missing or falsy)
        3. Get base context from cache
        4. Build final context: base → frontmatter vars → caller context
        5. If template file (has template extension):
           - Load and process partials
           - Render with Chevron
        6. Return RenderedContent (rendered or as-is)
    """
```

### Return Type

```python
@dataclass
class RenderedContent(Content):
    """Result of template rendering, extends Content with template metadata."""

    # Inherited from Content:
    # frontmatter: Dict[str, Any]
    # frontmatter_length: int
    # content: str
    # content_length: int

    # Template metadata
    template_path: Path
    template_name: str  # Display name without extension
```

## Implementation Details

### Package Structure

New package: `src/mcp_guide/render/`

```
src/mcp_guide/render/
  __init__.py          # Exports: render_template, RenderedContent
  template.py          # render_template() implementation
  content.py           # RenderedContent dataclass, frontmatter constants
```

**Dependencies** (from existing utils):
- `from mcp_guide.utils.file_discovery import FileInfo, TEMPLATE_EXTENSIONS`
- `from mcp_guide.utils.frontmatter import Content, parse_content_with_frontmatter`
- `from mcp_guide.utils.template_context import TemplateContext`
- `from mcp_guide.utils.template_renderer import render_template_content`

### Frontmatter Key Constants

Add to `src/mcp_guide/render/content.py`:

```python
# Frontmatter key constants
FM_INSTRUCTION = "instruction"
FM_TYPE = "type"
FM_DESCRIPTION = "description"
FM_REQUIRES_PREFIX = "requires-"
FM_CATEGORY = "category"
FM_USAGE = "usage"
FM_ALIASES = "aliases"
FM_INCLUDES = "includes"
```

Use these constants throughout the render package instead of string literals.

### Template Discovery

**Current behavior (keep as-is)**:
- `discover_category_files(base_dir, patterns)` handles discovery
- Supports glob patterns with automatic extension expansion
- Deduplicates template vs non-template versions
- Returns `FileInfo` objects with lazy content loading

**New behavior**:
- `render_template()` accepts either:
  - `str`: pattern for discovery (uses `discover_category_files`)
  - `FileInfo`: pre-discovered template (skips discovery)

### Frontmatter Processing

**Parsing** (existing):
```python
parsed = parse_content_with_frontmatter(content)
# Returns: Content(frontmatter, frontmatter_length, content, content_length)
```

**Requirements Checking**:
```python
# Check requires-* in frontmatter
for key, required_value in parsed.frontmatter.items():
    if not key.startswith(FM_REQUIRES_PREFIX):
        continue

    flag_name = key[len(FM_REQUIRES_PREFIX):]
    flag_value = project_flags.get(flag_name)

    # Flag not in project_flags or falsy → return None (filter out)
    if not flag_value:
        logger.debug(f"Template {file_info.path} filtered: requires-{flag_name} not met")
        return None
```

Simple: check each `requires-*` key, if flag missing or falsy → log and return None.

**Context Layering**:
```python
# Get base context from cache
from mcp_guide.utils.template_context_cache import get_template_contexts

base_context = await get_template_contexts()

# Extract frontmatter keys as context variables (exclude requires-* and includes)
frontmatter_vars = {
    k: v for k, v in parsed.frontmatter.items()
    if not k.startswith(FM_REQUIRES_PREFIX) and k != FM_INCLUDES
}

# Build final context: base → frontmatter vars → caller context
final_context = base_context
if frontmatter_vars:
    final_context = final_context.new_child(frontmatter_vars)
if context:
    final_context = final_context.new_child(context)
```

**Note on Frontmatter Field Rendering**:
The `instruction` field (and potentially other frontmatter fields) can contain template variables like `{{agent.prefix}}` or `{{workflow.file}}`. The current code in `guide_prompt.py` renders the instruction separately after rendering the main template, using the same context. This allows frontmatter values to be dynamic.

To avoid circular rendering (e.g., `instruction: "{{instruction}}"`), frontmatter vars are added to context **before** rendering, so they reference the raw frontmatter values, not rendered ones. The caller is responsible for rendering specific frontmatter fields if needed.

### Template Type Detection

Not needed - removed from design.

### Partial Handling

**Current behavior (reuse as-is)**:
- Partials loaded from frontmatter `includes` field
- Partial paths resolved relative to template directory
- Underscore prefix added to basename if not present
- Partials have their own frontmatter requirements checking
- Unmet requirements → empty content (partial skipped)

**Partial Resolution Example**:
```yaml
# Template: _commands/openspec/template.mustache
includes:
  - ../_partials/partial
```
```mustache
{{> partial}}
```
Resolves to: `_commands/_partials/_partial.mustache`

**Integration**:
- `render_template()` delegates to existing `render_template_content()`
- `render_template_content()` already handles partials correctly via `load_partial_content()`
- No changes needed to partial loading logic

### Template vs Non-Template Files

**Template files** (have template extension):
- Parse frontmatter
- Check requires-*
- Build context with frontmatter vars
- Load partials
- Render with Chevron

**Non-template files** (no template extension):
- Parse frontmatter
- Check requires-*
- Return content as-is (no rendering, no partials)

Same frontmatter rules apply to both.

### Error Handling

`render_template()` returns `Optional[RenderedContent]`:
- Returns `RenderedContent` if successful
- Returns `None` if requirements not met or any error occurs

No `Result` wrapper. Caller handles discovery and decides what to do with `None`.

## Implementation Strategy

### This Spec: Create New Renderer (No Refactoring)

1. **Create `src/mcp_guide/render/` package**
2. **Add `RenderedContent` dataclass** to `render/content.py` (extends `Content`)
3. **Add `REQUIRES_PREFIX` constant** to `render/content.py`
4. **Add `render_template()` function** to `render/template.py`
5. **Export from `render/__init__.py`**: `render_template`, `RenderedContent`
6. **Add tests** for new functions
7. **DO NOT touch existing functions** - they continue to work as-is
8. **DO NOT update any call sites** - that's for later specs

### Future Specs: Migrate Call Sites (One at a Time)

Each migration will be a separate spec:
- Migrate workflow template rendering
- Migrate common template rendering
- Migrate command help rendering
- Migrate category content rendering
- Remove old rendering functions (final cleanup)

## Testing Strategy

### Unit Tests (New Functions Only)

1. **Template Discovery**:
   - Pattern matching
   - FileInfo direct usage
   - Template not found errors

2. **Frontmatter Processing**:
   - Requirements checking
   - Context variable extraction and layering

3. **Template Type Detection**:
   - Path-based detection
   - Frontmatter override
   - Edge cases

4. **Rendering**:
   - Simple templates
   - Templates with partials
   - Templates with context variables
   - Templates with requirements

5. **Error Handling**:
   - Template not found
   - Requirements not met
   - Rendering errors
   - Batch error collection

### No Integration Tests Yet

Integration tests will be added when call sites are migrated in future specs.

## Design Decisions

### 1. RenderedContent instruction property

Add convenience property:
```python
@property
def instruction(self) -> Optional[str]:
    """Get instruction from frontmatter or default for template type."""
    return self.frontmatter.get(FM_INSTRUCTION, get_type_based_default_instruction(self.template_type))
```

Note: `get_type_based_default_instruction()` should handle missing/unknown types.
```

### 2. Rendering errors

Log and return None:
- Log error details for debugging
- Return `None` to indicate template unusable
- Caller doesn't need error details

### 3. Template type property

Add property with frontmatter fallback:
```python
@property
def template_type(self) -> str:
    """Get template type from frontmatter, default to agent/instruction."""
    return self.frontmatter.get(FM_TYPE, AGENT_INSTRUCTION)
```

No path inference - type is about intent, not location.

### 4. Context building

Renderer builds context:
- Get base context from cache (`get_template_contexts()`)
- Add frontmatter vars
- Add caller's injected context
- Render

Caller provides local context, renderer handles assembly.

## Summary

The template rendering system provides:

1. **Single entry point**: `render_template()` for all template types
2. **Consistent processing**: Same frontmatter rules, same context handling
3. **Clear separation**: Discovery → Parsing → Rendering → Output (caller)
4. **Rich metadata**: `RenderedContent` extends `Content` with template info
5. **No breaking changes**: New functions alongside existing ones
6. **Minimal design**: Only what's needed, no speculation

This spec creates the new renderer. Future specs will migrate call sites one by one.

The system does NOT:
- Touch any existing rendering functions
- Update any call sites
- Change existing discovery or frontmatter logic
- Break existing templates
- Add unnecessary complexity or features

## Final Implementation Notes

### Implementation Complete

**Date**: 2026-01-29

**Package**: `src/mcp_guide/render/`

**Modules**:
- `__init__.py` - Exports: `render_template`, `RenderedContent`, frontmatter constants
- `content.py` - `RenderedContent` dataclass, 8 frontmatter constants
- `template.py` - `render_template()` function

**Key Implementation Details**:

1. **Context Layering**: Implemented as designed - base → frontmatter vars → caller context using `TemplateContext.new_child()`

2. **requires-* Filtering**: Simple check - if flag missing or falsy, return None immediately

3. **Template Detection**: Delegates to existing `is_template_file(FileInfo)` - checks for `.mustache`, `.hbs`, `.handlebars` extensions

4. **Error Handling**: All errors caught, logged, and return None - no Result wrapper

5. **Type Safety**: Added assertion for mypy: `assert result.value is not None` after success check

6. **Frontmatter Constants**: All 8 constants defined and used throughout render package

**Test Coverage**:
- 10 tests covering all core functionality
- 100% coverage on `content.py`
- 83% coverage on `template.py`
- All tests passing

**Code Quality**:
- Ruff format: ✓
- Ruff check: ✓
- Mypy (render package): ✓
- Bandit: ✓

**Not Implemented** (as per design):
- No call site migrations (future specs)
- No changes to existing rendering functions
- No integration tests (added when call sites migrate)
Jus