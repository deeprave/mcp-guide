# Template Rendering System Analysis

## Current Architecture

### Core Components

#### 1. Template Discovery (`file_discovery.py`)
- **Function**: `discover_category_files(category_dir, patterns)`
- **Purpose**: Find files matching glob patterns in a directory
- **Features**:
  - Supports template extensions: `.mustache`, `.hbs`, `.handlebars`, `.chevron`
  - Auto-expands patterns to include extension variants
  - Deduplicates: prefers non-template over template versions
  - Returns `FileInfo` objects with metadata (path, size, mtime, etc.)
  - Lazy-loads content and frontmatter via async accessors

#### 2. Frontmatter Processing (`frontmatter.py`)
- **Function**: `parse_content_with_frontmatter(content)`
- **Returns**: `Content` dataclass with:
  - `frontmatter`: Dict of YAML metadata
  - `frontmatter_length`: Character count of frontmatter section
  - `content`: Content without frontmatter
  - `content_length`: Character count of content
- **Function**: `check_frontmatter_requirements(frontmatter, context)`
  - Evaluates `requires-*` fields against context
  - Returns `True` if requirements met, `False` to suppress content

#### 3. Template Rendering (`template_renderer.py`)

**Low-level**: `render_template_content(content, context, ...)`
- Accepts raw template string
- Processes frontmatter metadata
- Loads partials from frontmatter `includes`
- Injects template functions (format_date, truncate, etc.)
- Renders with Chevron
- Returns `Result[str]`

**Mid-level**: `render_file_content(file_info, context, base_dir, docroot)`
- Accepts `FileInfo` object
- Loads content if needed
- Parses frontmatter
- Delegates to `render_template_content`
- Returns `Result[str]`

#### 4. System Content Rendering (`system_content.py`)
- **Function**: `render_system_content(system_dir, pattern, context, docroot)`
- Discovers files matching pattern in system_dir
- Uses first match
- Renders via `render_file_content`
- Returns `Result[str]`

#### 5. Specialized Renderers (`workflow/rendering.py`)

**`render_workflow_template(template_pattern)`**:
- System dir: `{docroot}/_workflow`
- Context: from `get_template_contexts()`
- Delegates to `render_system_content`

**`render_common_template(template_pattern, extra_context)`**:
- System dir: `{docroot}/_common`
- Context: base + optional extra_context layered on top
- Delegates to `render_system_content`

### Template Context System

#### TemplateContext (`template_context.py`)
- Extends `ChainMap[str, Any]` for scope chaining
- Converts lists to `IndexedList` for iteration + indexed access
- Validates all keys are strings
- Supports `new_child()` for layered contexts

#### Template Context Cache (`template_context_cache.py`)
- Singleton cache: `_template_context_cache`
- Builds system context with:
  - Project data
  - Categories/collections
  - Workflow state
  - OpenSpec data
  - Client info
  - Feature flags
- Function: `get_template_contexts()` returns cached context

### Content Utilities (`content_utils.py`)

**`read_and_render_file_contents(files, base_dir, docroot, template_context, category_prefix)`**:
- Reads content for list of `FileInfo` objects
- Parses frontmatter
- Checks frontmatter requirements → filters files
- Renders templates if context provided
- Updates content_size after rendering
- Applies category prefix to names
- Returns list of error messages

**`extract_and_deduplicate_instructions(files)`**:
- Extracts `instruction` field from frontmatter
- Handles important instructions (prefix `!`) that override regular ones
- Deduplicates instructions
- Returns combined instruction string

### Current Rendering Paths

#### Path 1: Command Help
```
guide_prompt.py:get_command_help()
  → discover_category_files(commands_dir, [pattern])
  → render_template_content(help_template_content, context)
```

#### Path 2: Workflow Templates
```
openspec_task.py / tasks.py
  → render_workflow_template(template_pattern)
    → render_system_content(workflow_dir, pattern, context, docroot)
      → discover_category_files(system_dir, [pattern])
      → render_file_content(file_info, context, system_dir, docroot)
```

#### Path 3: Common Templates
```
openspec_task.py / tasks.py
  → render_common_template(template_pattern, extra_context)
    → render_system_content(common_dir, pattern, context, docroot)
      → discover_category_files(system_dir, [pattern])
      → render_file_content(file_info, context, system_dir, docroot)
```

#### Path 4: Category Content
```
tool_content.py:internal_get_content()
  → gather_content(session, project, expression)
    → discover_category_files(category_dir, patterns)
    → read_and_render_file_contents(files, base_dir, docroot, template_context)
      → render_file_content(file_info, template_context, base_dir, docroot)
```

## Current Issues

### 1. Fragmentation
- Multiple entry points: `render_workflow_template`, `render_common_template`, direct `render_file_content` calls
- Inconsistent context building (some add extra_context, some don't)
- Different discovery patterns for different template types

### 2. Inconsistent Frontmatter Handling
- Some paths check requirements during discovery
- Some paths check requirements during rendering
- Partial loading has its own frontmatter checking

### 3. Template Type Routing
- Template type determined by directory location
- No explicit type metadata
- Hard-coded paths in specialized renderers

### 4. Context Management
- Context built differently for different template types
- Extra context layering is ad-hoc
- No clear separation between base context and injected context

## Proposed Unified System

### Design Goals
1. **Single entry point** for all template rendering
2. **Consistent frontmatter processing** across all template types
3. **Explicit template type handling** with clear routing
4. **Separation of concerns**: discovery → parsing → rendering
5. **Caller controls output handling** (no assumptions about what to do with rendered content)

### High-Level Architecture

```python
# Discovery phase (unchanged)
files = await discover_category_files(base_dir, patterns)

# Rendering phase (new unified interface)
for file_info in files:
    rendered = await render_template(
        template=file_info,  # or pattern/name
        base_dir=base_dir,
        context=base_context,
        injected_context=extra_context,  # optional
    )
    # rendered is RenderedTemplate with:
    #   - frontmatter: Dict
    #   - content: str
    #   - content_length: int
    #   - frontmatter_length: int
    #   - template_type: str (command/workflow/openspec/common/category)
    #   - metadata: Dict (any additional info)
```

### Key Components

#### 1. Unified Renderer
```python
async def render_template(
    template: FileInfo | str,  # FileInfo or pattern
    base_dir: Path,
    context: TemplateContext,
    injected_context: Optional[Dict[str, Any]] = None,
    docroot: Optional[Path] = None,
) -> Result[RenderedTemplate]:
    """
    Unified template rendering with consistent frontmatter handling.

    Steps:
    1. Discover template if pattern provided
    2. Load and parse frontmatter
    3. Check frontmatter requirements
    4. Build final context (base + injected + frontmatter)
    5. Load and process partials
    6. Render template
    7. Return RenderedTemplate
    """
```

#### 2. RenderedTemplate Dataclass
```python
@dataclass
class RenderedTemplate:
    """Result of template rendering."""
    content: str
    frontmatter: Dict[str, Any]
    content_length: int
    frontmatter_length: int
    template_type: str  # command/workflow/openspec/common/category
    template_path: Path
    metadata: Dict[str, Any]  # extensible metadata
```

#### 3. Template Type Detection
```python
def detect_template_type(file_path: Path, docroot: Path) -> str:
    """
    Detect template type from path relative to docroot.

    Rules:
    - _commands/** → "command"
    - _workflow/** → "workflow"
    - _common/** → "common"
    - openspec/** → "openspec"
    - categories/** → "category"
    """
```

### Migration Strategy

#### Phase 1: Create Unified Interface
- Implement `render_template()` function
- Implement `RenderedTemplate` dataclass
- Implement template type detection
- Keep existing functions as wrappers

#### Phase 2: Update Call Sites
- Replace `render_workflow_template()` calls
- Replace `render_common_template()` calls
- Replace direct `render_file_content()` calls
- Update content tools

#### Phase 3: Cleanup
- Remove deprecated functions
- Update tests
- Update documentation

## Open Questions

1. **Should template type be in frontmatter or inferred from location?**
   - Current: inferred from location
   - Proposal: keep inference, allow frontmatter override

2. **How to handle batch rendering?**
   - Current: `read_and_render_file_contents()` processes multiple files
   - Proposal: keep batch function, have it call unified renderer

3. **Should RenderedTemplate include instruction field?**
   - Current: instructions extracted separately
   - Proposal: include in metadata, let caller extract

4. **How to handle partial requirements checking?**
   - Current: checked during partial loading
   - Proposal: keep current behavior, ensure consistency

5. **Should context building be part of renderer or caller responsibility?**
   - Current: mixed (some renderers build context, some accept it)
   - Proposal: caller builds context, renderer accepts it
