# Template Rendering API

Unified template rendering with frontmatter and context handling.

## Core Functions

### render_template()

```python
async def render_template(
    file_info: FileInfo,
    base_dir: Path,
    project_flags: Dict[str, Any],
    context: Optional[TemplateContext] = None,
    docroot: Optional[Path] = None,
) -> Optional[RenderedContent]
```

**Returns**: `RenderedContent` if successful, `None` if filtered by `requires-*` directives

**Raises**:
- `RuntimeError`: Template rendering fails (syntax errors, rendering exceptions)
- `FileNotFoundError`: Template file does not exist
- `PermissionError`: Insufficient permissions to read template
- `UnicodeDecodeError`: Template file is not valid UTF-8

**Process**:
1. Parse frontmatter
2. Check `requires-*` directives against `project_flags` (return `None` if not met)
3. Build context: base → frontmatter vars → caller context
4. Render template files with Chevron and partials support

### process_frontmatter()

```python
async def process_frontmatter(
    content: str,
    requirements_context: Dict[str, Any],
    render_context: Optional[TemplateContext],
) -> Optional[ProcessedFrontmatter]
```

**Returns**: `ProcessedFrontmatter` if requirements met, `None` if filtered

**Process**:
1. Parse frontmatter from content
2. Check `requires-*` directives against requirements_context
3. Render `instruction` and `description` fields as templates if render_context provided

Used internally by `render_template()` and `process_file()` for consistent frontmatter handling.

### process_file()

```python
async def process_file(
    file_info: FileInfo,
    base_dir: Path,
    requirements_context: Dict[str, Any],
    render_context: Optional[TemplateContext],
) -> Optional[ProcessedFrontmatter]
```

**Returns**: `ProcessedFrontmatter` if requirements met, `None` if filtered

**Process**:
1. Read file content
2. Process frontmatter using `process_frontmatter()`

**Note**: For non-template files only. Templates must use `render_template()` for proper partials support.

## Exception Handling

The API raises exceptions for errors rather than returning `None`. Callers should handle exceptions appropriately:

```python
try:
    result = await render_template(
        file_info=file_info,
        base_dir=base_dir,
        project_flags=project_flags,
        context=context,
    )

    if result is None:
        # File filtered by requires-* (not an error)
        continue

    # Use rendered content
    process(result.content)

except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
    # File I/O errors
    logger.error(f"Failed to read template {file_info.path}: {e}")
    # Handle error appropriately

except Exception as e:
    # Unexpected errors - log with full traceback
    logger.exception(f"Unexpected error rendering {file_info.path}")
    # Decide whether to continue or abort
```

**Key Points**:
- `None` return = filtered by requirements (not an error)
- Exceptions = actual errors that need handling
- Use `logger.exception()` to capture full traceback for unexpected errors
- Use `logger.error()` for expected file I/O errors
- Catch specific exceptions first, then broader `Exception` for unexpected errors
- In batch processing, catch exceptions per-file to prevent one error from terminating the batch

**Batch Processing**:
```python
results = []
for file_info in files:
    try:
        rendered = await render_template(...)
        if rendered is None:
            continue  # Filtered by requires-*
        results.append(rendered)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        logger.error(f"File error: {file_info.path}: {e}")
        continue
    except Exception as e:
        logger.exception(f"Unexpected error: {file_info.path}")
        continue
```

## Return Type

```python
@dataclass
class RenderedContent(Content):
    template_path: Path
    template_name: str

    @property
    def template_type(self) -> str

    @property
    def instruction(self) -> Optional[str]
```

Extends `Content` (frontmatter, content, lengths) with template metadata.

## Frontmatter Constants

```python
FM_INSTRUCTION = "instruction"
FM_TYPE = "type"
FM_DESCRIPTION = "description"
FM_REQUIRES_PREFIX = "requires-"
FM_CATEGORY = "category"
FM_USAGE = "usage"
FM_ALIASES = "aliases"
FM_INCLUDES = "includes"
```

## Usage

```python
from mcp_guide.render import render_template, RenderedContent

result = await render_template(
    file_info=file_info,
    base_dir=Path("templates"),
    project_flags={"feature": True},
    context=TemplateContext({"var": "value"}),
)

if result:
    print(result.content)
    print(result.instruction)
```
