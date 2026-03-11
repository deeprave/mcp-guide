"""Tests for process_frontmatter function."""

import pytest

from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import process_frontmatter


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
