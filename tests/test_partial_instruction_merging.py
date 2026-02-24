"""Tests for partial frontmatter instruction merging."""

from datetime import datetime

import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.template import render_template


@pytest.mark.asyncio
class TestPartialInstructionMerging:
    """Test that partial frontmatter instructions are properly merged with parent instructions."""

    async def test_partial_important_instruction_overrides_parent(self, tmp_path):
        """Test that partial with important instruction (^) overrides parent instruction."""
        # Create parent template with regular instruction
        parent_file = tmp_path / "parent.mustache"
        parent_file.write_text(
            "---\ntype: agent/instruction\ninstruction: Parent instruction\nincludes:\n  - child\n---\n{{>child}}"
        )

        # Create partial with important instruction
        partial_file = tmp_path / "_child.mustache"
        partial_file.write_text(
            "---\ntype: agent/instruction\ninstruction: '^ Important child instruction'\n---\nChild content"
        )

        file_info = FileInfo(
            path=parent_file,
            size=parent_file.stat().st_size,
            content_size=100,
            mtime=datetime.now(),
            name="parent.mustache",
        )

        result = await render_template(file_info, tmp_path, {})

        assert result is not None
        # Important instruction from partial should override parent
        assert result.instruction == "Important child instruction"

    async def test_partial_regular_instruction_does_not_override_parent(self, tmp_path):
        """Test that partial with regular instruction is combined with parent instruction."""
        # Create parent template with regular instruction
        parent_file = tmp_path / "parent.mustache"
        parent_file.write_text(
            "---\ntype: agent/instruction\ninstruction: Parent instruction\nincludes:\n  - child\n---\n{{>child}}"
        )

        # Create partial with regular (non-important) instruction
        partial_file = tmp_path / "_child.mustache"
        partial_file.write_text(
            "---\ntype: agent/instruction\ninstruction: Child regular instruction\n---\nChild content"
        )

        file_info = FileInfo(
            path=parent_file,
            size=parent_file.stat().st_size,
            content_size=100,
            mtime=datetime.now(),
            name="parent.mustache",
        )

        result = await render_template(file_info, tmp_path, {})

        assert result is not None
        # Regular instructions are combined (not overridden)
        assert "Parent instruction" in result.instruction
        assert "Child regular instruction" in result.instruction

    async def test_multiple_partials_with_mixed_instructions(self, tmp_path):
        """Test combining instructions from multiple partials with mixed importance."""
        # Create parent template
        parent_file = tmp_path / "parent.mustache"
        parent_file.write_text(
            "---\ntype: agent/instruction\ninstruction: Parent instruction\nincludes:\n  - child1\n  - child2\n---\n{{>child1}}{{>child2}}"
        )

        # Create first partial with regular instruction
        partial1_file = tmp_path / "_child1.mustache"
        partial1_file.write_text("---\ntype: agent/instruction\ninstruction: Child1 regular\n---\nChild1 content")

        # Create second partial with important instruction
        partial2_file = tmp_path / "_child2.mustache"
        partial2_file.write_text("---\ntype: agent/instruction\ninstruction: '^ Child2 important'\n---\nChild2 content")

        file_info = FileInfo(
            path=parent_file,
            size=parent_file.stat().st_size,
            content_size=100,
            mtime=datetime.now(),
            name="parent.mustache",
        )

        result = await render_template(file_info, tmp_path, {})

        assert result is not None
        # Important instruction from child2 should override all others
        assert result.instruction == "Child2 important"

    async def test_partial_without_instruction_does_not_affect_parent(self, tmp_path):
        """Test that partial without instruction doesn't affect parent instruction."""
        # Create parent template with instruction
        parent_file = tmp_path / "parent.mustache"
        parent_file.write_text(
            "---\ntype: agent/instruction\ninstruction: Parent instruction\nincludes:\n  - child\n---\n{{>child}}"
        )

        # Create partial without instruction (user/information type has default instruction)
        partial_file = tmp_path / "_child.mustache"
        partial_file.write_text("---\ntype: user/information\n---\nChild content")

        file_info = FileInfo(
            path=parent_file,
            size=parent_file.stat().st_size,
            content_size=100,
            mtime=datetime.now(),
            name="parent.mustache",
        )

        result = await render_template(file_info, tmp_path, {})

        assert result is not None
        # Parent instruction should be present
        assert "Parent instruction" in result.instruction
        # user/information type has default instruction that gets combined
        assert "This information is to be presented to the user, not actioned." in result.instruction

    async def test_parent_without_instruction_uses_partial_instruction(self, tmp_path):
        """Test that when parent has no instruction, partial instruction is used."""
        # Create parent template without instruction (user/information has default)
        parent_file = tmp_path / "parent.mustache"
        parent_file.write_text("---\ntype: user/information\nincludes:\n  - child\n---\n{{>child}}")

        # Create partial with instruction
        partial_file = tmp_path / "_child.mustache"
        partial_file.write_text("---\ntype: agent/instruction\ninstruction: Child instruction\n---\nChild content")

        file_info = FileInfo(
            path=parent_file,
            size=parent_file.stat().st_size,
            content_size=100,
            mtime=datetime.now(),
            name="parent.mustache",
        )

        result = await render_template(file_info, tmp_path, {})

        assert result is not None
        # Should combine parent's default instruction with partial's instruction
        assert "Child instruction" in result.instruction
        assert "This information is to be presented to the user, not actioned." in result.instruction

    async def test_fuzzy_deduplication_removes_similar_instructions(self, tmp_path):
        """Test that similar instructions from multiple partials are deduplicated."""
        # Create parent template
        parent_file = tmp_path / "parent.mustache"
        parent_file.write_text(
            "---\ntype: agent/instruction\ninstruction: Follow this policy.\nincludes:\n  - child1\n  - child2\n---\n{{>child1}}{{>child2}}"
        )

        # Create first partial with similar instruction
        partial1_file = tmp_path / "_child1.mustache"
        partial1_file.write_text("---\ntype: agent/instruction\ninstruction: Follow this policy.\n---\nChild1 content")

        # Create second partial with slightly different but similar instruction
        partial2_file = tmp_path / "_child2.mustache"
        partial2_file.write_text("---\ntype: agent/instruction\ninstruction: Follow this policy\n---\nChild2 content")

        file_info = FileInfo(
            path=parent_file,
            size=parent_file.stat().st_size,
            content_size=100,
            mtime=datetime.now(),
            name="parent.mustache",
        )

        result = await render_template(file_info, tmp_path, {})

        assert result is not None
        # Should deduplicate similar instructions (fuzzy matching at 85% threshold)
        assert result.instruction == "Follow this policy."
