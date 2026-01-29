# Template Rendering API

Unified template rendering with frontmatter and context handling.

## Core Function

```python
async def render_template(
    file_info: FileInfo,
    base_dir: Path,
    project_flags: Dict[str, Any],
    context: Optional[TemplateContext] = None,
    docroot: Optional[Path] = None,
) -> Optional[RenderedContent]
```

**Returns**: `RenderedContent` if successful, `None` if filtered or error

**Process**:
1. Parse frontmatter
2. Check `requires-*` directives against `project_flags` (return `None` if not met)
3. Build context: base → frontmatter vars → caller context
4. Render template files with Chevron, return non-template files as-is

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
