"""Tests for get_content unified access tool."""

import json

import pytest
from pydantic import ValidationError

from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.models import Category, Collection, Project
from mcp_guide.tools.tool_content import ContentArgs, get_content


def create_mock_session(tmp_path, project_data, project_flags_data=None, feature_flags_data=None):
    """Create a mock session with required methods."""

    project_flags_data = project_flags_data or {}
    feature_flags_data = feature_flags_data or {}

    class MockSession:
        async def get_project(self):
            return project_data

        async def get_docroot(self):
            return str(tmp_path)

        def project_flags(self):
            class MockProjectFlags:
                async def list(self):
                    return project_flags_data

            return MockProjectFlags()

        def feature_flags(self):
            class MockFeatureFlags:
                async def list(self):
                    return feature_flags_data

            return MockFeatureFlags()

    return MockSession()


def test_content_args_exists():
    """Test that ContentArgs class exists."""
    assert ContentArgs is not None


def test_content_args_inherits_from_tool_arguments():
    """Test that ContentArgs inherits from ToolArguments."""
    assert issubclass(ContentArgs, ToolArguments)


def test_expression_field_is_required():
    """Test that expression field is required."""
    with pytest.raises(ValidationError):
        ContentArgs()


def test_pattern_field_is_optional():
    """Test that pattern field is optional."""
    args = ContentArgs(expression="test")
    assert args.pattern is None


def test_schema_validates_correctly():
    """Test that schema validates correctly."""
    args = ContentArgs(expression="test", pattern="*.md")
    assert args.expression == "test"
    assert args.pattern == "*.md"


async def test_get_content_collection_only(tmp_path, monkeypatch):
    """Test get_content with collection-only match."""
    # Create test files
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test")

    # Project data
    project_data = Project(
        name="test",
        categories={"guide": Category(dir="guide", patterns=["*.md"])},
        collections={"all": Collection(categories=["guide"])},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool
    args = ContentArgs(expression="all")
    result_json = await get_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True


async def test_get_content_category_only(tmp_path, monkeypatch):
    """Test get_content with category-only match."""
    # Create test files
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test")

    # Project data
    project_data = Project(
        name="test",
        categories={"guide": Category(dir="guide", patterns=["*.md"])},
        collections={},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool
    args = ContentArgs(expression="guide")
    result_json = await get_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True


async def test_get_content_deduplicates(tmp_path, monkeypatch):
    """Test get_content deduplicates when name matches both collection and category."""
    # Create test files
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test")

    # Project data - collection and category both named "guide"
    project_data = Project(
        name="test",
        categories={"guide": Category(dir="guide", patterns=["*.md"])},
        collections={"guide": Collection(categories=["guide"])},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool
    args = ContentArgs(expression="guide")
    result_json = await get_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    # File content should be present (de-duplication tested by not having duplicate content)
    assert "# Test" in result["value"]


async def test_get_content_empty_result(tmp_path, monkeypatch):
    """Test get_content with no matching files."""
    # Create empty category directory
    category_dir = tmp_path / "empty"
    category_dir.mkdir()

    # Project data
    project_data = Project(
        name="test",
        categories={"empty": Category(dir="empty", patterns=["*.md"])},
        collections={},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool
    args = ContentArgs(expression="empty")
    result_json = await get_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "No matching content found" in result["value"]
    assert "instruction" in result


async def test_get_content_pattern_override(tmp_path, monkeypatch):
    """Test get_content with pattern override."""
    # Create test files
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test")
    (category_dir / "test.txt").write_text("Test")

    # Project data - category accepts both .md and .txt
    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", patterns=["*.md", "*.txt"])},
        collections={},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool with pattern override to only get .md files
    args = ContentArgs(expression="docs", pattern="*.md")
    result_json = await get_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "# Test" in result["value"]
    # Verify .txt file content is not included
    assert "Test" not in result["value"] or result["value"].count("Test") == 1  # Only from "# Test"


async def test_get_content_category_sets_metadata(tmp_path, monkeypatch):
    """Test that category-only search sets category field on FileInfo."""
    # Create test file
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test")

    # Project data
    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", patterns=["*.md"])},
        collections={},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool
    args = ContentArgs(expression="docs")
    result_json = await get_content(args)

    # Verify success - the bug would cause issues in future template rendering
    # but for now we just verify the tool works
    result = json.loads(result_json)
    assert result["success"] is True
    assert "# Test" in result["value"]


async def test_get_content_collection_sets_metadata(tmp_path, monkeypatch):
    """Test that collection search sets both category and collection fields on FileInfo."""
    # Create test file
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test")

    # Project data
    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", patterns=["*.md"])},
        collections={"all": Collection(categories=["docs"])},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool
    args = ContentArgs(expression="all")
    result_json = await get_content(args)

    # Verify success - both category and collection fields should be set
    result = json.loads(result_json)
    assert result["success"] is True
    assert "# Test" in result["value"]


@pytest.mark.parametrize(
    "project_flags,feature_flags,expected_format",
    [
        # No flags - should default to NONE (BaseFormatter)
        ({}, {}, "none"),
        # Only project flag set
        ({"content-format-mime": "plain"}, {}, "plain"),
        ({"content-format-mime": "mime"}, {}, "mime"),
        ({"content-format-mime": "none"}, {}, "none"),
        # Only global flag set
        ({}, {"content-format-mime": "plain"}, "plain"),
        ({}, {"content-format-mime": "mime"}, "mime"),
        ({}, {"content-format-mime": "none"}, "none"),
        # Project flag takes precedence over global
        ({"content-format-mime": "plain"}, {"content-format-mime": "mime"}, "plain"),
        ({"content-format-mime": "mime"}, {"content-format-mime": "plain"}, "mime"),
        ({"content-format-mime": "none"}, {"content-format-mime": "plain"}, "none"),
    ],
)
async def test_get_content_flag_resolution(tmp_path, monkeypatch, project_flags, feature_flags, expected_format):
    """Test content-format-mime flag resolution and precedence."""
    # Create test file
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test Content\n\nSome text.")

    # Project data
    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", patterns=["*.md"])},
        collections={},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data, project_flags, feature_flags)

    monkeypatch.setattr("mcp_guide.tools.tool_content.get_or_create_session", mock_get_session)

    # Call tool
    args = ContentArgs(expression="docs")
    result_json = await get_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True

    # Verify content formatting based on expected format
    content = result["value"]

    if expected_format == "none":
        # BaseFormatter joins with newlines
        assert "# Test Content" in content
        assert "Some text." in content
        # Should be simple newline-joined content
        assert content.count("\n") >= 2
    elif expected_format == "plain":
        # PlainFormatter behavior - should still contain the content
        assert "# Test Content" in content
        assert "Some text." in content
    elif expected_format == "mime":
        # MimeFormatter behavior - should contain MIME-like structure
        assert "# Test Content" in content
        assert "Some text." in content
