"""Tests for frontmatter instruction handling functionality."""

import unittest
from datetime import datetime
from pathlib import Path

from mcp_guide.utils.content_utils import extract_and_deduplicate_instructions
from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.frontmatter import (
    AGENT_INFO,
    AGENT_INSTRUCTION,
    USER_INFO,
    get_frontmatter_instruction,
    get_frontmatter_partials,
    get_frontmatter_type,
    get_type_based_default_instruction,
    parse_frontmatter_content,
    validate_content_type,
)


class TestContentTypeConstants:
    """Test content type constants and validation."""

    def test_content_type_constants(self):
        """Test that constants are defined correctly."""
        assert USER_INFO == "user/information"
        assert AGENT_INFO == "agent/information"
        assert AGENT_INSTRUCTION == "agent/instruction"

    def test_validate_content_type(self):
        """Test content type validation."""
        # Test valid types
        assert validate_content_type("user/information") is True
        assert validate_content_type("agent/information") is True
        assert validate_content_type("agent/instruction") is True

        # Test invalid types
        assert validate_content_type("invalid/type") is False
        assert validate_content_type(None) is False
        assert validate_content_type("") is False


class TestFrontmatterExtraction(unittest.TestCase):
    """Test frontmatter extraction functions."""

    def test_get_frontmatter_instruction(self):
        """Test instruction extraction from frontmatter."""
        frontmatter = {"instruction": "Process this content carefully"}
        assert get_frontmatter_instruction(frontmatter) == "Process this content carefully"

        # Test missing instruction
        assert get_frontmatter_instruction({}) is None
        assert get_frontmatter_instruction(None) is None

    def test_get_frontmatter_type_with_validation(self):
        """Test that get_frontmatter_type validates and warns about invalid types."""
        # Test valid type
        frontmatter = {"type": "agent/instruction"}
        assert get_frontmatter_type(frontmatter) == "agent/instruction"

        # Test invalid type with warning
        with self.assertLogs("mcp_guide.utils.frontmatter", level="WARNING") as log:
            frontmatter = {"type": "invalid/type"}
            result = get_frontmatter_type(frontmatter)
            assert result == "user/information"  # Falls back to default
            assert "Unknown content type 'invalid/type'" in log.output[0]

    def test_get_frontmatter_type(self):
        """Test content type extraction from frontmatter."""
        frontmatter = {"type": "agent/instruction"}
        assert get_frontmatter_type(frontmatter) == "agent/instruction"

        # Test missing type (defaults to user/information)
        assert get_frontmatter_type({}) == "user/information"
        assert get_frontmatter_type(None) == "user/information"

    def test_get_frontmatter_partials(self):
        """Test partials extraction from frontmatter."""
        frontmatter = {"partials": {"header": "templates/partials/header.md", "footer": "templates/partials/footer.md"}}
        partials = get_frontmatter_partials(frontmatter)
        assert partials["header"] == "templates/partials/header.md"
        assert partials["footer"] == "templates/partials/footer.md"

        # Test missing partials
        assert get_frontmatter_partials({}) == {}
        assert get_frontmatter_partials(None) == {}


class TestTypeBasedInstructions:
    """Test type-based default instruction logic."""

    def test_get_type_based_default_instruction(self):
        """Test default instructions for different content types."""
        assert get_type_based_default_instruction("user/information") == "Display this information to the user"
        assert (
            get_type_based_default_instruction("agent/information")
            == "For your information and use. Do not display this content to the user."
        )
        assert get_type_based_default_instruction("agent/instruction") is None  # Should use explicit instruction

        # Test unknown type defaults to user/information
        assert get_type_based_default_instruction("unknown/type") == "Display this information to the user"


class TestContentStripping:
    """Test frontmatter stripping from content."""

    def test_parse_frontmatter_content_strips_frontmatter(self):
        """Test that frontmatter is stripped from content output."""
        content = """---
type: agent/instruction
instruction: "Process this carefully"
---
# Main Content
This is the actual content."""

        metadata, clean_content = parse_frontmatter_content(content)

        # Content should not contain frontmatter
        assert "---" not in clean_content
        assert "type: agent/instruction" not in clean_content
        assert "# Main Content" in clean_content
        assert "This is the actual content." in clean_content

        # Metadata should contain frontmatter
        assert metadata["type"] == "agent/instruction"
        assert metadata["instruction"] == "Process this carefully"

    def test_parse_frontmatter_content_no_frontmatter(self):
        """Test content without frontmatter."""
        content = """# Main Content
This is content without frontmatter."""

        metadata, clean_content = parse_frontmatter_content(content)

        # Should return None metadata and unchanged content
        assert metadata is None
        assert clean_content == content

    def test_parse_frontmatter_content_unterminated_frontmatter(self):
        """Test content with unterminated frontmatter."""
        content = """---
type: agent/instruction
instruction: "Missing closing delimiter"
# Main Content
This content has unterminated frontmatter."""

        metadata, clean_content = parse_frontmatter_content(content)

        # Should return None metadata and unchanged content
        assert metadata is None
        assert clean_content == content

    def test_parse_frontmatter_content_malformed_yaml(self):
        """Test content with malformed YAML frontmatter."""
        content = """---
type: agent/instruction
instruction: "Missing quote
invalid: yaml: structure
---
# Main Content
This content has malformed YAML."""

        metadata, clean_content = parse_frontmatter_content(content)

        # Should return None metadata but still strip the malformed frontmatter section
        assert metadata is None
        assert clean_content == "# Main Content\nThis content has malformed YAML."


class TestInstructionExtraction:
    """Test instruction extraction and deduplication."""

    def test_instruction_extraction_single_document(self):
        """Test explicit instruction extraction."""
        file_info = FileInfo(
            path=Path("test.md"),
            size=100,
            content_size=100,
            mtime=datetime.now(),
            name="test.md",
            frontmatter={"type": "agent/instruction", "instruction": "Custom instruction here"},
        )

        instruction = extract_and_deduplicate_instructions([file_info])
        assert instruction == "Custom instruction here"

    def test_instruction_deduplication_multiple_documents(self):
        """Test instruction deduplication across multiple docs."""
        file1 = FileInfo(
            path=Path("test1.md"),
            size=100,
            content_size=100,
            mtime=datetime.now(),
            name="test1.md",
            frontmatter={"instruction": "Same instruction"},
        )

        file2 = FileInfo(
            path=Path("test2.md"),
            size=200,
            content_size=200,
            mtime=datetime.now(),
            name="test2.md",
            frontmatter={"instruction": "Same instruction"},
        )

        instruction = extract_and_deduplicate_instructions([file1, file2])
        assert instruction == "Same instruction"  # Not duplicated

    def test_mixed_content_types(self):
        """Test mixed content types with different instructions."""
        user_file = FileInfo(
            path=Path("user.md"),
            size=100,
            content_size=100,
            mtime=datetime.now(),
            name="user.md",
            frontmatter={"type": "user/information"},
        )

        agent_file = FileInfo(
            path=Path("agent.md"),
            size=200,
            content_size=200,
            mtime=datetime.now(),
            name="agent.md",
            frontmatter={"type": "agent/information"},
        )

        instruction = extract_and_deduplicate_instructions([user_file, agent_file])
        # Should combine instructions in insertion order (user first, then agent)
        assert (
            instruction
            == "Display this information to the user\nFor your information and use. Do not display this content to the user."
        )

    def test_no_frontmatter_files(self):
        """Test files without frontmatter."""
        file_info = FileInfo(
            path=Path("test.md"), size=100, content_size=100, mtime=datetime.now(), name="test.md", frontmatter=None
        )

        instruction = extract_and_deduplicate_instructions([file_info])
        assert instruction is None

    def test_important_instruction_overrides_regular(self):
        """Test that important instructions override regular ones."""
        regular_file = FileInfo(
            path=Path("regular.md"),
            size=100,
            content_size=100,
            mtime=datetime.now(),
            name="regular.md",
            frontmatter={"instruction": "Regular instruction"},
        )

        important_file = FileInfo(
            path=Path("important.md"),
            size=200,
            content_size=200,
            mtime=datetime.now(),
            name="important.md",
            frontmatter={"instruction": "! Important instruction"},
        )

        instruction = extract_and_deduplicate_instructions([regular_file, important_file])
        assert instruction == "Important instruction"  # Only important, regular ignored

    def test_multiple_important_instructions(self):
        """Test multiple important instructions are combined."""
        important_file1 = FileInfo(
            path=Path("important1.md"),
            size=100,
            content_size=100,
            mtime=datetime.now(),
            name="important1.md",
            frontmatter={"instruction": "!First important"},
        )

        important_file2 = FileInfo(
            path=Path("important2.md"),
            size=200,
            content_size=200,
            mtime=datetime.now(),
            name="important2.md",
            frontmatter={"instruction": "! Second important"},
        )

        instruction = extract_and_deduplicate_instructions([important_file1, important_file2])
        assert instruction == "First important\nSecond important"

    def test_important_instruction_whitespace_handling(self):
        """Test important instruction whitespace is properly removed."""
        file_info = FileInfo(
            path=Path("test.md"),
            size=100,
            content_size=100,
            mtime=datetime.now(),
            name="test.md",
            frontmatter={"instruction": "!   Instruction with spaces"},
        )

        instruction = extract_and_deduplicate_instructions([file_info])
        assert instruction == "Instruction with spaces"
