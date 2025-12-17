"""Tests for frontmatter parsing utilities."""

import pytest

from mcp_guide.utils.frontmatter import extract_frontmatter, get_frontmatter_description


class TestExtractFrontmatter:
    """Test extract_frontmatter function."""

    @pytest.mark.asyncio
    async def test_valid_frontmatter(self, tmp_path):
        """Test parsing valid YAML frontmatter."""
        content = """---
title: Test Document
description: A test document
author: Test Author
---
# Content here"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path)

        assert metadata == {"title": "Test Document", "description": "A test document", "author": "Test Author"}
        assert length == 78  # Actual length of frontmatter including delimiters

    @pytest.mark.asyncio
    async def test_no_frontmatter(self, tmp_path):
        """Test file without frontmatter."""
        content = "# Just content\nNo frontmatter here"

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path)

        assert metadata is None
        assert length == 0

    @pytest.mark.asyncio
    async def test_empty_frontmatter(self, tmp_path):
        """Test empty frontmatter block."""
        content = """---
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path)

        assert metadata is None  # Empty YAML returns None from yaml.safe_load
        assert length == 0

    @pytest.mark.asyncio
    async def test_malformed_yaml(self, tmp_path):
        """Test malformed YAML in frontmatter."""
        content = """---
title: Test
invalid: [unclosed
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path)

        assert metadata is None
        assert length == 0

    @pytest.mark.asyncio
    async def test_incomplete_frontmatter(self, tmp_path):
        """Test frontmatter without closing delimiter."""
        content = """---
title: Test
description: No closing delimiter
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path)

        assert metadata is None
        assert length == 0

    @pytest.mark.asyncio
    async def test_max_read_size_boundary(self, tmp_path):
        """Test frontmatter at max_read_size boundary."""
        # Create frontmatter that's exactly at the boundary
        frontmatter = "---\ntitle: Test\n---\n"
        content = frontmatter + "x" * 4000  # Total > 4096 chars

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path, max_read_size=20)

        assert metadata == {"title": "Test"}
        assert length == len(frontmatter)

    @pytest.mark.asyncio
    async def test_frontmatter_beyond_max_read_size(self, tmp_path):
        """Test frontmatter that extends beyond max_read_size."""
        content = "---\ntitle: Test\n" + "x" * 100 + "\n---\n# Content"

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path, max_read_size=20)

        assert metadata is None
        assert length == 0

    @pytest.mark.asyncio
    async def test_different_line_endings(self, tmp_path):
        """Test frontmatter with different line endings."""
        content = "---\r\ntitle: Test\r\ndescription: Windows line endings\r\n---\r\n# Content"

        file_path = tmp_path / "test.md"
        file_path.write_text(content, newline="")  # Preserve exact line endings

        metadata, length = await extract_frontmatter(file_path)

        assert metadata == {"title": "Test", "description": "Windows line endings"}
        assert length > 0

    @pytest.mark.asyncio
    async def test_non_dict_yaml(self, tmp_path):
        """Test YAML that doesn't parse to a dict."""
        content = """---
- item1
- item2
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, length = await extract_frontmatter(file_path)

        assert metadata is None
        assert length == 0

    @pytest.mark.asyncio
    async def test_file_not_found(self, tmp_path):
        """Test handling of non-existent file."""
        file_path = tmp_path / "nonexistent.md"

        metadata, length = await extract_frontmatter(file_path)

        assert metadata is None
        assert length == 0


class TestGetFrontmatterDescription:
    """Test get_frontmatter_description function."""

    @pytest.mark.asyncio
    async def test_lowercase_description(self, tmp_path):
        """Test extracting lowercase description field."""
        content = """---
title: Test
description: Test description
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description == "Test description"

    @pytest.mark.asyncio
    async def test_uppercase_description(self, tmp_path):
        """Test extracting uppercase description field (case-insensitive)."""
        content = """---
title: Test
DESCRIPTION: Test description uppercase
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description == "Test description uppercase"

    @pytest.mark.asyncio
    async def test_mixed_case_description(self, tmp_path):
        """Test extracting mixed case description field."""
        content = """---
title: Test
Description: Test description mixed case
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description == "Test description mixed case"

    @pytest.mark.asyncio
    async def test_no_description_field(self, tmp_path):
        """Test file with frontmatter but no description field."""
        content = """---
title: Test
author: Test Author
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description is None

    @pytest.mark.asyncio
    async def test_null_description_value(self, tmp_path):
        """Test description field with null value."""
        content = """---
title: Test
description: null
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description is None

    @pytest.mark.asyncio
    async def test_empty_description_value(self, tmp_path):
        """Test description field with empty string value."""
        content = """---
title: Test
description: ""
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description == ""

    @pytest.mark.asyncio
    async def test_numeric_description_value(self, tmp_path):
        """Test description field with numeric value (converted to string)."""
        content = """---
title: Test
description: 123
---
# Content"""

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description == "123"

    @pytest.mark.asyncio
    async def test_no_frontmatter_returns_none(self, tmp_path):
        """Test file without frontmatter returns None."""
        content = "# Just content\nNo frontmatter here"

        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        description = await get_frontmatter_description(file_path)

        assert description is None
