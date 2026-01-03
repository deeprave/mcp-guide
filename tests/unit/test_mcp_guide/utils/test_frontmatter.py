"""Tests for unified frontmatter parsing utilities."""

import pytest

from mcp_guide.utils.frontmatter import (
    Content,
    get_frontmatter_instruction,
    parse_content_with_frontmatter,
    read_content_with_frontmatter,
)


class TestParseContentWithFrontmatter:
    """Test parse_content_with_frontmatter function."""

    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        content = "# Hello\nThis is content"
        result = parse_content_with_frontmatter(content)

        assert result.frontmatter == {}
        assert result.frontmatter_length == 0
        assert result.content == content
        assert result.content_length == len(content)

    def test_valid_frontmatter(self):
        """Test content with valid frontmatter."""
        content = """---
title: Test
description: A test file
---
# Hello
This is content"""

        result = parse_content_with_frontmatter(content)

        assert result.frontmatter == {"title": "Test", "description": "A test file"}
        assert result.frontmatter_length == 45  # Length of frontmatter block
        assert result.content == "# Hello\nThis is content"
        assert result.content_length == 23

    def test_case_insensitive_keys(self):
        """Test that frontmatter keys are normalized to lowercase."""
        content = """---
Title: Test
DESCRIPTION: A test file
Instruction: Do something
---
Content here"""

        result = parse_content_with_frontmatter(content)

        assert result.frontmatter == {"title": "Test", "description": "A test file", "instruction": "Do something"}

    def test_invalid_yaml(self):
        """Test handling of invalid YAML in frontmatter."""
        content = """---
title: Test
invalid: [unclosed
---
Content here"""

        result = parse_content_with_frontmatter(content)

        assert result.frontmatter == {}
        assert result.content == "Content here"

    def test_incomplete_frontmatter(self):
        """Test content with incomplete frontmatter (no closing ---)."""
        content = """---
title: Test
description: No closing delimiter
Content here"""

        result = parse_content_with_frontmatter(content)

        assert result.frontmatter == {}
        assert result.frontmatter_length == 0
        assert result.content == content
        assert result.content_length == len(content)

    def test_empty_frontmatter(self):
        """Test content with empty frontmatter."""
        content = """---
---
Content here"""

        result = parse_content_with_frontmatter(content)

        assert result.frontmatter == {}
        assert result.frontmatter_length == 8  # "---\n---\n"
        assert result.content == "Content here"


class TestReadContentWithFrontmatter:
    """Test read_content_with_frontmatter function."""

    @pytest.mark.asyncio
    async def test_read_valid_file(self, tmp_path):
        """Test reading a file with frontmatter."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test File
type: user/information
---
# Test Content
This is a test."""

        test_file.write_text(content)

        result = await read_content_with_frontmatter(test_file)

        assert result.frontmatter == {"title": "Test File", "type": "user/information"}
        assert result.content == "# Test Content\nThis is a test."

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, tmp_path):
        """Test reading a nonexistent file."""
        nonexistent = tmp_path / "nonexistent.md"

        result = await read_content_with_frontmatter(nonexistent)

        assert result.frontmatter == {}
        assert result.frontmatter_length == 0
        assert result.content == ""
        assert result.content_length == 0


class TestGetFrontmatterInstruction:
    """Test get_frontmatter_instruction function."""

    def test_with_instruction(self):
        """Test extracting instruction from frontmatter."""
        frontmatter = {"instruction": "Do something", "title": "Test"}
        result = get_frontmatter_instruction(frontmatter)
        assert result == "Do something"

    def test_without_instruction(self):
        """Test frontmatter without instruction."""
        frontmatter = {"title": "Test", "description": "A test"}
        result = get_frontmatter_instruction(frontmatter)
        assert result is None

    def test_none_frontmatter(self):
        """Test with None frontmatter."""
        result = get_frontmatter_instruction(None)
        assert result is None

    def test_empty_frontmatter(self):
        """Test with empty frontmatter."""
        result = get_frontmatter_instruction({})
        assert result is None


class TestContentDataclass:
    """Test Content dataclass."""

    def test_content_creation(self):
        """Test creating Content object."""
        content = Content(
            frontmatter={"title": "Test"}, frontmatter_length=20, content="Hello world", content_length=11
        )

        assert content.frontmatter == {"title": "Test"}
        assert content.frontmatter_length == 20
        assert content.content == "Hello world"
        assert content.content_length == 11
