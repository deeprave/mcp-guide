"""Tests for process_frontmatter function."""

import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import process_file, process_frontmatter


@pytest.mark.asyncio
async def test_process_frontmatter_basic():
    """Test basic frontmatter parsing without requirements."""
    content = """---
type: agent/instruction
instruction: Test instruction
---
Content here"""

    result = await process_frontmatter(content, {}, None)

    assert result is not None
    assert result.frontmatter["type"] == "agent/instruction"
    assert result.frontmatter["instruction"] == "Test instruction"
    assert result.content == "Content here"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "requirements_context,expected_none",
    [
        ({"feature": True}, False),  # requirements met
        ({"feature": False}, True),  # requirements not met
    ],
)
async def test_process_frontmatter_requirements(requirements_context, expected_none):
    """Test frontmatter with requirements checking."""
    content = """---
requires-feature: true
---
Content"""

    result = await process_frontmatter(content, requirements_context, None)

    if expected_none:
        assert result is None
    else:
        assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_name,template,context_data,expected",
    [
        ("instruction", "Hello {{name}}", {"name": "World"}, "Hello World"),
        ("description", "Project {{project}}", {"project": "test"}, "Project test"),
    ],
)
async def test_process_frontmatter_render_fields(field_name, template, context_data, expected):
    """Test frontmatter fields rendered as templates."""
    content = f"""---
{field_name}: {template}
---
Content"""
    context = TemplateContext(context_data)

    result = await process_frontmatter(content, {}, context)

    assert result is not None
    assert result.frontmatter[field_name] == expected


@pytest.mark.asyncio
async def test_process_frontmatter_render_error_graceful():
    """Test rendering error handled gracefully with warning."""
    content = """---
instruction: Hello {{missing}}
---
Content"""

    result = await process_frontmatter(content, {}, TemplateContext({}))

    # Should not raise, should log warning
    assert result is not None


@pytest.mark.asyncio
async def test_process_file_non_template(tmp_path):
    """Test process_file with a non-template markdown file."""
    # Create a simple markdown file
    file_path = tmp_path / "test.md"
    file_path.write_text("# Hello\n\nContent here")

    stat = file_path.stat()
    from datetime import datetime

    file_info = FileInfo(
        path=file_path,
        size=stat.st_size,
        content_size=stat.st_size,
        mtime=datetime.fromtimestamp(stat.st_mtime),
        name="test.md",
    )

    result = await process_file(file_info, tmp_path, {}, None)

    assert result is not None
    assert result.content == "# Hello\n\nContent here"
    assert result.frontmatter == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "requirements_context,expected_none",
    [
        ({"feature": True}, False),  # requirements met
        ({"feature": False}, True),  # requirements not met
    ],
)
async def test_process_file_with_frontmatter_requirements(tmp_path, requirements_context, expected_none):
    """Test process_file with frontmatter requirements checking."""
    file_path = tmp_path / "test.md"
    file_path.write_text("""---
requires-feature: true
---
Content""")

    stat = file_path.stat()
    from datetime import datetime

    file_info = FileInfo(
        path=file_path,
        size=stat.st_size,
        content_size=stat.st_size,
        mtime=datetime.fromtimestamp(stat.st_mtime),
        name="test.md",
    )

    result = await process_file(file_info, tmp_path, requirements_context, None)

    if expected_none:
        assert result is None
    else:
        assert result is not None
        assert result.content == "Content"
