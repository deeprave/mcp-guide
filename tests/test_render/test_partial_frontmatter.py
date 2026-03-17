"""Tests for partial frontmatter handling."""

import pytest

from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.render.partials import load_partial_content
from mcp_guide.render.renderer import render_template_content


@pytest.mark.anyio
class TestPartialFrontmatter:
    """Test partial loading with frontmatter."""

    async def test_load_partial_returns_frontmatter(self, tmp_path):
        """Test that load_partial_content returns frontmatter."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\ntype: user/information\ninstruction: '^ Display this'\n---\nContent here")

        content, frontmatter = await load_partial_content(partial_file, tmp_path)
        assert content == "Content here"
        assert isinstance(frontmatter, Frontmatter)
        assert frontmatter.get("type") == "user/information"
        assert frontmatter.get("instruction") == "^ Display this"

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


@pytest.mark.anyio
async def test_partial_regular_instruction_does_not_override_parent(tmp_path):
    """Test that partial with regular instruction does not override parent instruction."""

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


@pytest.mark.anyio
async def test_partial_instruction_rendered_with_context(tmp_path):
    """Test that partial instruction/description fields are rendered as templates."""
    partial_file = tmp_path / "_test.mustache"
    partial_file.write_text("---\ninstruction: 'Hello {{name}}'\ndescription: 'Project {{project}}'\n---\nContent")

    context = {"name": "World", "project": "test"}
    content, frontmatter = await load_partial_content(partial_file, tmp_path, context)

    assert content == "Content"
    assert frontmatter.get("instruction") == "Hello World"
    assert frontmatter.get("description") == "Project test"


@pytest.mark.anyio
async def test_unused_partial_instruction_not_applied(tmp_path):
    """Bug fix: partial instruction must NOT be applied when partial isn't rendered.

    If a partial is in the includes list but {{>partial}} is not in the template body,
    chevron never renders it, so its frontmatter should not be collected.
    """

    # Template does NOT reference {{>client-info}}
    template_content = "Status: OK"

    # Partial with important instruction exists in includes
    partial_path = tmp_path / "_client-info.mustache"
    partial_path.write_text(
        "---\ntype: agent/instruction\ninstruction: '^ Run client_info tool'\n---\nAgent detection required"
    )

    metadata = Frontmatter({"type": "user/information", "includes": ["client-info"]})
    context = TemplateContext({})

    result = await render_template_content(
        template_content,
        context,
        file_path=str(tmp_path / "status.mustache"),
        metadata=dict(metadata),
        base_dir=tmp_path,
    )

    assert result.is_ok()
    rendered_content, partial_frontmatter_list, _ = result.value
    assert rendered_content == "Status: OK"
    # Partial was NOT rendered, so its frontmatter must NOT be in the list
    assert partial_frontmatter_list == []


@pytest.mark.anyio
async def test_used_partial_instruction_is_applied(tmp_path):
    """Partial instruction IS applied when partial is actually rendered via {{>partial}}."""

    # Template DOES reference {{>client-info}}
    template_content = "Status: {{>client-info}}"

    partial_path = tmp_path / "_client-info.mustache"
    partial_path.write_text(
        "---\ntype: agent/instruction\ninstruction: '^ Run client_info tool'\n---\nAgent detection required"
    )

    metadata = Frontmatter({"type": "user/information", "includes": ["client-info"]})
    context = TemplateContext({})

    result = await render_template_content(
        template_content,
        context,
        file_path=str(tmp_path / "status.mustache"),
        metadata=dict(metadata),
        base_dir=tmp_path,
    )

    assert result.is_ok()
    rendered_content, partial_frontmatter_list, _ = result.value
    assert "Agent detection required" in rendered_content
    # Partial WAS rendered, so its frontmatter must be collected
    assert len(partial_frontmatter_list) == 1
    assert partial_frontmatter_list[0].get("instruction") == "^ Run client_info tool"


@pytest.mark.anyio
async def test_partial_instruction_placeholders_resolved(tmp_path):
    """Bug fix: placeholders like {{tool_prefix}} in partial instructions must be resolved."""

    template_content = "{{>agent-detect}}"

    partial_path = tmp_path / "_agent-detect.mustache"
    partial_path.write_text(
        "---\ntype: agent/instruction\ninstruction: 'Run {{tool_prefix}}client_info'\n---\nDetect agent"
    )

    metadata = Frontmatter({"includes": ["agent-detect"]})
    context = TemplateContext({"tool_prefix": "my_"})

    result = await render_template_content(
        template_content,
        context,
        file_path=str(tmp_path / "parent.mustache"),
        metadata=dict(metadata),
        base_dir=tmp_path,
    )

    assert result.is_ok()
    _, partial_frontmatter_list, _ = result.value
    assert len(partial_frontmatter_list) == 1
    # Placeholder must be resolved
    assert partial_frontmatter_list[0].get("instruction") == "Run my_client_info"
