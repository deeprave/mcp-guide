"""Tests for partial frontmatter handling."""

import pytest

from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.render.partials import load_partial_content


@pytest.mark.asyncio
class TestPartialFrontmatter:
    """Test partial loading with frontmatter."""

    async def test_load_partial_returns_frontmatter(self, tmp_path):
        """Test that load_partial_content returns frontmatter."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\ntype: user/information\ninstruction: '! Display this'\n---\nContent here")

        content, frontmatter = await load_partial_content(partial_file, tmp_path)
        assert content == "Content here"
        assert isinstance(frontmatter, Frontmatter)
        assert frontmatter.get("type") == "user/information"
        assert frontmatter.get("instruction") == "! Display this"

    async def test_load_partial_without_frontmatter(self, tmp_path):
        """Test partial without frontmatter returns empty dict."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("Just content")

        content, frontmatter = await load_partial_content(partial_file, tmp_path)
        assert content == "Just content"
        assert isinstance(frontmatter, Frontmatter)
        assert len(frontmatter) == 0

    async def test_load_partial_with_requirements_met(self, tmp_path):
        """Test partial with met requirements returns content and frontmatter."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\nrequires-feature: enabled\ninstruction: Show this\n---\nContent")

        context = {"feature": "enabled"}
        content, frontmatter = await load_partial_content(partial_file, tmp_path, context)
        assert content == "Content"
        assert frontmatter.get("instruction") == "Show this"

    async def test_load_partial_with_requirements_not_met(self, tmp_path):
        """Test partial with unmet requirements returns empty content."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\nrequires-feature: enabled\ninstruction: Show this\n---\nContent")

        context = {"feature": "disabled"}
        content, frontmatter = await load_partial_content(partial_file, tmp_path, context)
        assert content == ""
        # Frontmatter should still be returned even if requirements not met
        assert frontmatter.get("instruction") == "Show this"


@pytest.mark.asyncio
async def test_partial_important_instruction_overrides_parent(tmp_path):
    """Test that partial with important instruction overrides parent instruction."""
    from mcp_guide.render.renderer import render_template_content

    # Create parent template with regular instruction
    parent_content = "{{>child}}"
    parent_metadata = Frontmatter({"instruction": "Parent instruction"})

    # Create partial with important instruction
    partial_path = tmp_path / "_child.mustache"
    partial_path.write_text("---\ninstruction: '! Child overrides'\n---\nChild content")

    # Render with includes
    parent_metadata["includes"] = ["child"]
    result = await render_template_content(
        parent_content,
        {},
        file_path=str(tmp_path / "parent.mustache"),
        metadata=parent_metadata,
        base_dir=tmp_path,
    )

    assert result.is_ok()
    # Parent metadata should be updated with child's important instruction
    assert parent_metadata["instruction"] == "! Child overrides"


@pytest.mark.asyncio
async def test_partial_regular_instruction_does_not_override_parent(tmp_path):
    """Test that partial with regular instruction does not override parent instruction."""
    from mcp_guide.render.renderer import render_template_content

    # Create parent template with regular instruction
    parent_content = "{{>child}}"
    parent_metadata = Frontmatter({"instruction": "Parent instruction"})

    # Create partial with regular (non-important) instruction
    partial_path = tmp_path / "_child.mustache"
    partial_path.write_text("---\ninstruction: 'Child regular instruction'\n---\nChild content")

    # Render with includes
    parent_metadata["includes"] = ["child"]
    result = await render_template_content(
        parent_content,
        {},
        file_path=str(tmp_path / "parent.mustache"),
        metadata=parent_metadata,
        base_dir=tmp_path,
    )

    assert result.is_ok()
    # Parent metadata should NOT be changed by child's regular instruction
    assert parent_metadata["instruction"] == "Parent instruction"
