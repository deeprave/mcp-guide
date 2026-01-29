"""Tests for render.content module."""

from pathlib import Path

from mcp_guide.render.content import (
    FM_ALIASES,
    FM_CATEGORY,
    FM_DESCRIPTION,
    FM_INCLUDES,
    FM_INSTRUCTION,
    FM_REQUIRES_PREFIX,
    FM_TYPE,
    FM_USAGE,
    RenderedContent,
)
from mcp_guide.utils.frontmatter import Content
from mcp_guide.utils.frontmatter_types import Frontmatter


def test_frontmatter_constants_exist():
    """Test that all frontmatter constants are defined with correct values."""
    assert FM_INSTRUCTION == "instruction"
    assert FM_TYPE == "type"
    assert FM_DESCRIPTION == "description"
    assert FM_REQUIRES_PREFIX == "requires-"
    assert FM_CATEGORY == "category"
    assert FM_USAGE == "usage"
    assert FM_ALIASES == "aliases"
    assert FM_INCLUDES == "includes"


def test_rendered_content_creation():
    """Test RenderedContent can be created and inherits from Content."""
    frontmatter = Frontmatter({"type": "agent-instruction"})
    content = "Test content"
    template_path = Path("/test/template.mustache")
    template_name = "template.mustache"

    rendered = RenderedContent(
        frontmatter=frontmatter,
        frontmatter_length=10,
        content=content,
        content_length=len(content),
        template_path=template_path,
        template_name=template_name,
    )

    assert isinstance(rendered, Content)
    assert rendered.frontmatter == frontmatter
    assert rendered.content == content
    assert rendered.template_path == template_path
    assert rendered.template_name == template_name


def test_instruction_property_with_frontmatter():
    """Test instruction property returns frontmatter value when present."""
    frontmatter = Frontmatter({"instruction": "Custom instruction"})
    rendered = RenderedContent(
        frontmatter=frontmatter,
        frontmatter_length=10,
        content="Test",
        content_length=4,
        template_path=Path("/test.mustache"),
        template_name="test.mustache",
    )
    assert rendered.instruction == "custom instruction"  # lowercase


def test_instruction_property_without_frontmatter():
    """Test instruction property returns default when not in frontmatter."""
    frontmatter = Frontmatter({"type": "agent-instruction"})
    rendered = RenderedContent(
        frontmatter=frontmatter,
        frontmatter_length=10,
        content="Test",
        content_length=4,
        template_path=Path("/test.mustache"),
        template_name="test.mustache",
    )
    assert rendered.instruction is not None


def test_template_type_property_with_frontmatter():
    """Test template_type property returns frontmatter value when present."""
    frontmatter = Frontmatter({"type": "custom-type"})
    rendered = RenderedContent(
        frontmatter=frontmatter,
        frontmatter_length=10,
        content="Test",
        content_length=4,
        template_path=Path("/test.mustache"),
        template_name="test.mustache",
    )
    assert rendered.template_type == "custom-type"


def test_template_type_property_without_frontmatter():
    """Test template_type property returns default when not in frontmatter."""
    frontmatter = Frontmatter()
    rendered = RenderedContent(
        frontmatter=frontmatter,
        frontmatter_length=10,
        content="Test",
        content_length=4,
        template_path=Path("/test.mustache"),
        template_name="test.mustache",
    )
    assert rendered.template_type == "agent/instruction"
