"""Tests for centralized instruction resolution."""

from mcp_guide.render.frontmatter import resolve_instruction


class TestResolveInstruction:
    """Test centralized instruction resolution function."""

    def test_explicit_instruction(self):
        """Test explicit instruction from frontmatter."""
        frontmatter = {"instruction": "Display this content"}
        instruction, is_important = resolve_instruction(frontmatter)
        assert instruction == "Display this content"
        assert is_important is False

    def test_important_instruction_with_prefix(self):
        """Test important instruction with ^ prefix."""
        frontmatter = {"instruction": "^ Override parent instruction"}
        instruction, is_important = resolve_instruction(frontmatter)
        assert instruction == "Override parent instruction"
        assert is_important is True

    def test_important_instruction_with_whitespace(self):
        """Test important instruction with ^ prefix and extra whitespace."""
        frontmatter = {"instruction": "^   Override with spaces"}
        instruction, is_important = resolve_instruction(frontmatter)
        assert instruction == "Override with spaces"
        assert is_important is True

    def test_empty_after_prefix_removal(self):
        """Test instruction that is empty after ^ prefix removal."""
        frontmatter = {"instruction": "^"}
        instruction, is_important = resolve_instruction(frontmatter)
        assert instruction is None
        assert is_important is True

    def test_no_instruction_with_type(self):
        """Test type-based default when no explicit instruction."""
        frontmatter = {"type": "user/information"}
        instruction, is_important = resolve_instruction(frontmatter, "user/information")
        assert instruction is not None  # Should get type-based default
        assert is_important is False

    def test_no_instruction_no_type(self):
        """Test fallback when no instruction and no type."""
        frontmatter = {}
        instruction, is_important = resolve_instruction(frontmatter)
        assert instruction is not None  # Should get default
        assert is_important is False

    def test_none_frontmatter(self):
        """Test with None frontmatter."""
        instruction, is_important = resolve_instruction(None)
        assert instruction is not None  # Should get default
        assert is_important is False

    def test_empty_frontmatter(self):
        """Test with empty frontmatter dict."""
        instruction, is_important = resolve_instruction({})
        assert instruction is not None  # Should get default
        assert is_important is False

    def test_non_string_instruction(self):
        """Test with non-string instruction value."""
        frontmatter = {"instruction": 123}
        instruction, is_important = resolve_instruction(frontmatter)
        assert instruction is not None  # Should get default
        assert is_important is False
