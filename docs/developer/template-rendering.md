# Template Rendering Guide

This guide explains how to work with templates and frontmatter in mcp-guide.

## Overview

mcp-guide uses Mustache/Chevron templates with YAML frontmatter for dynamic content generation. The rendering system provides three core functions for different use cases:

- **render_template()** - Render complete templates with partials support
- **process_frontmatter()** - Parse and process frontmatter with requirements checking
- **process_file()** - Read and process non-template files

## Template Files

Templates are Mustache files (`.mustache` extension) with optional YAML frontmatter:

```mustache
---
type: agent/instruction
description: Brief description of the template
requires-feature: workflow
---
# Template Content

Hello {{name}}!

{{#items}}
- {{value}}
{{/items}}
```

> **Note**: lists are represented internally as objects as:
> ```python
> {
>   value: str,       # value of the item
>   first: bool,      # true if first in list, otherwise false
>   last: bool        # true if last in list, otherwise false
> }
> ```
> This allows smart formatting since you can add a prefix to the first item,
> `{{#first}}prefix{{/first}}{{value}}`
> and add text between each iten
> `{{value}}{{^last}}, {{/last}}`

### Frontmatter Fields

Common frontmatter fields:

- **type**: Content type (`user/information`, `agent/information`, `agent/instruction`)
- **description**: Brief description (rendered as template)
- **instruction**: Custom instruction for agents (rendered as template)
- **requires-***: Conditional requirements (e.g., `requires-workflow: true`)
- **includes**: List of partial templates to include
-
> **Note**:

All frontmatter keys are case-insensitive and normalized to lowercase.

## Rendering Templates

### render_template()

Use `render_template()` for complete template rendering with partials support:

```python
from mcp_guide.render import render_template
from mcp_guide.render.context import TemplateContext

result = await render_template(
    file_info=file_info,
    base_dir=Path("templates"),
    project_flags={"feature": True},
    context=TemplateContext({"name": "World"}),
)

if result:
    print(result.content)
    print(result.instruction)
```

**Returns**: `RenderedContent` if successful, `None` if filtered by `requires-*` directives

**Raises**:
- `RuntimeError`: Template rendering fails
- `FileNotFoundError`: Template file not found
- `PermissionError`: Insufficient permissions
- `UnicodeDecodeError`: Invalid UTF-8

**Process**:
1. Parse frontmatter
2. Check `requires-*` directives against `project_flags`
3. Build context: base → frontmatter vars → caller context
4. Render template with Chevron and partials

### process_frontmatter()

Use `process_frontmatter()` for frontmatter processing without file I/O:

```python
from mcp_guide.render.frontmatter import process_frontmatter

processed = await process_frontmatter(
    content=raw_content,
    requirements_context={"feature": True},
    render_context=TemplateContext({"name": "World"}),
)

if processed:
    print(processed.frontmatter)
    print(processed.content)
```

**Returns**: `ProcessedFrontmatter` if requirements met, `None` if filtered

**Process**:
1. Parse frontmatter from content
2. Check `requires-*` directives
3. Render `instruction` and `description` fields as templates

### process_file()

Use `process_file()` for non-template files:

```python
from mcp_guide.render.frontmatter import process_file

processed = await process_file(
    file_info=file_info,
    base_dir=Path("."),
    requirements_context={"feature": True},
    render_context=TemplateContext({"name": "World"}),
)

if processed:
    print(processed.content)
```

**Returns**: `ProcessedFrontmatter` if requirements met, `None` if filtered

**Note**: For non-template files only. Templates must use `render_template()` for proper partials support.

## Requirements Checking

Use `requires-*` frontmatter fields to conditionally include content:

```yaml
---
type: agent/instruction
requires-feature: workflow
requires-openspec: true
---
```

Content is filtered out (returns `None`) if any requirement is not met.

## Exception Handling

The rendering API raises exceptions for errors rather than returning `None`:

```python
try:
    result = await render_template(
        file_info=file_info,
        base_dir=base_dir,
        project_flags=project_flags,
        context=context,
    )

    if result is None:
        # Filtered by requires-* (not an error)
        continue

    # Use rendered content
    process(result.content)

except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
    # File I/O errors
    logger.error(f"Failed to read template: {e}")

except Exception as e:
    # Unexpected errors
    logger.exception(f"Unexpected error rendering template")
```

**Key Points**:
- `None` return = filtered by requirements (not an error)
- Exceptions = actual errors that need handling
- Use `logger.exception()` for unexpected errors
- Use `logger.error()` for expected file I/O errors

## Batch Processing

When processing multiple files, catch exceptions per-file to prevent one error from terminating the batch:

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

## Return Types

### RenderedContent

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

### ProcessedFrontmatter

```python
@dataclass
class ProcessedFrontmatter:
    frontmatter: Frontmatter
    content: str
    frontmatter_length: int
    content_length: int
```

Contains parsed frontmatter and content without template-specific metadata.

## Frontmatter Constants

```python
from mcp_guide.render.content import (
    FM_INSTRUCTION,
    FM_TYPE,
    FM_DESCRIPTION,
    FM_REQUIRES_PREFIX,
    FM_CATEGORY,
    FM_USAGE,
    FM_ALIASES,
    FM_INCLUDES,
)
```

Use these constants when accessing frontmatter fields to ensure consistency.

## Best Practices

1. **Use render_template() for templates** - Always use `render_template()` for `.mustache` files to ensure partials work correctly
2. **Use process_file() for non-templates** - Use `process_file()` for markdown and other non-template files
3. **Handle None returns** - Check for `None` returns (filtered content) before using results
4. **Catch specific exceptions** - Catch file I/O exceptions separately from unexpected errors
5. **Use case-insensitive keys** - Frontmatter keys are normalized to lowercase
6. **Declare argrequired** - Use `argrequired` frontmatter field for flags that need space-separated values

## See Also

- [Command Authoring Guide](command-authoring.md) - Creating custom commands
- [Content Management](../user/content-management.md) - Working with content
