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
async def test_process_frontmatter_requirements_met():
    """Test frontmatter with satisfied requirements."""
    content = """---
requires-feature: true
---
Content"""

    result = await process_frontmatter(content, {"feature": True}, None)

    assert result is not None


@pytest.mark.asyncio
async def test_process_frontmatter_requirements_not_met():
    """Test frontmatter with unsatisfied requirements returns None."""
    content = """---
requires-feature: true
---
Content"""

    result = await process_frontmatter(content, {"feature": False}, None)

    assert result is None


@pytest.mark.asyncio
async def test_process_frontmatter_render_instruction():
    """Test instruction field rendered as template."""
    content = """---
instruction: Hello {{name}}
---
Content"""
    context = TemplateContext({"name": "World"})

    result = await process_frontmatter(content, {}, context)

    assert result is not None
    assert result.frontmatter["instruction"] == "Hello World"


@pytest.mark.asyncio
async def test_process_frontmatter_render_description():
    """Test description field rendered as template."""
    content = """---
description: Project {{project}}
---
Content"""
    context = TemplateContext({"project": "test"})

    result = await process_frontmatter(content, {}, context)

    assert result is not None
    assert result.frontmatter["description"] == "Project test"


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
async def test_process_file_with_frontmatter_requirements_met(tmp_path):
    """Test process_file with frontmatter requirements that are satisfied."""
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

    result = await process_file(file_info, tmp_path, {"feature": True}, None)

    assert result is not None
    assert result.content == "Content"


@pytest.mark.asyncio
async def test_process_file_with_frontmatter_requirements_not_met(tmp_path):
    """Test process_file returns None when requirements not satisfied."""
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

    result = await process_file(file_info, tmp_path, {"feature": False}, None)

    assert result is None
