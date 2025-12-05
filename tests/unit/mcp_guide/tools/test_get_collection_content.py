"""Tests for get_collection_content tool."""


def test_collection_content_args_exists():
    """Test that CollectionContentArgs class exists."""
    from mcp_guide.tools.tool_collection import CollectionContentArgs

    assert CollectionContentArgs is not None


def test_collection_field_is_required():
    """Test that collection field is required."""
    import pytest
    from pydantic import ValidationError

    from mcp_guide.tools.tool_collection import CollectionContentArgs

    with pytest.raises(ValidationError):
        CollectionContentArgs()


def test_pattern_field_is_optional():
    """Test that pattern field is optional."""
    from mcp_guide.tools.tool_collection import CollectionContentArgs

    args = CollectionContentArgs(collection="docs")
    assert args.collection == "docs"
    assert args.pattern is None


def test_schema_validates_correctly():
    """Test that schema validates with valid data."""
    from mcp_guide.tools.tool_collection import CollectionContentArgs

    args = CollectionContentArgs(collection="docs", pattern="*.md")
    assert args.collection == "docs"
    assert args.pattern == "*.md"


async def test_get_collection_content_function_exists():
    """Test that get_collection_content function exists."""
    from mcp_guide.tools.tool_collection import get_collection_content

    assert get_collection_content is not None
    assert callable(get_collection_content)


async def test_tool_returns_result_ok_on_success(tmp_path, monkeypatch):
    """Test that tool returns Result.ok() with content on success."""
    import json

    from mcp_guide.models import Category, Collection, Project
    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Create test files
    (tmp_path / "test.md").write_text("# Test Content")

    # Create test project with category and collection
    project = Project(
        name="test",
        categories=[Category(name="docs", dir=".", patterns=["*.md"])],
        collections=[Collection(name="all-docs", categories=["docs"])],
    )

    # Mock session
    class MockSession:
        async def get_project(self):
            return project

        def get_docroot(self):
            return str(tmp_path)

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool
    args = CollectionContentArgs(collection="all-docs")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "value" in result
    assert "Test Content" in result["value"]


async def test_collection_not_found_returns_failure(tmp_path, monkeypatch):
    """Test that non-existent collection returns failure."""
    import json

    from mcp_guide.models import Project
    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Create test project with no collections
    project = Project(name="test", categories=[], collections=[])

    # Mock session
    class MockSession:
        async def get_project(self):
            return project

        def get_docroot(self):
            return str(tmp_path)

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool
    args = CollectionContentArgs(collection="nonexistent")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == "not_found"
    assert "nonexistent" in result["error"]


async def test_category_not_found_returns_failure(tmp_path, monkeypatch):
    """Test that collection with non-existent category returns failure."""
    import json

    from mcp_guide.models import Collection, Project
    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Create test project with collection referencing non-existent category
    project = Project(
        name="test",
        categories=[],
        collections=[Collection(name="test-collection", categories=["nonexistent"])],
    )

    # Mock session
    class MockSession:
        async def get_project(self):
            return project

        def get_docroot(self):
            return str(tmp_path)

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool
    args = CollectionContentArgs(collection="test-collection")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == "not_found"
    assert "category" in result["error"].lower()


async def test_no_matches_returns_success_with_message(tmp_path, monkeypatch):
    """Test that no matching files returns success with message."""
    import json

    from mcp_guide.models import Category, Collection, Project
    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Create test project with category and collection but no matching files
    project = Project(
        name="test",
        categories=[Category(name="docs", dir=".", patterns=["*.md"])],
        collections=[Collection(name="all-docs", categories=["docs"])],
    )

    # Mock session
    class MockSession:
        async def get_project(self):
            return project

        def get_docroot(self):
            return str(tmp_path)

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool
    args = CollectionContentArgs(collection="all-docs")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "no matching content" in result["value"].lower()


async def test_pattern_override_filters_files(tmp_path, monkeypatch):
    """Test that pattern parameter overrides category patterns."""
    import json

    from mcp_guide.models import Category, Collection, Project
    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Create test files
    (tmp_path / "test.md").write_text("# Markdown")
    (tmp_path / "test.txt").write_text("Text file")

    # Create test project with category matching both file types
    project = Project(
        name="test",
        categories=[Category(name="docs", dir=".", patterns=["*.md", "*.txt"])],
        collections=[Collection(name="all-docs", categories=["docs"])],
    )

    # Mock session
    class MockSession:
        async def get_project(self):
            return project

        def get_docroot(self):
            return str(tmp_path)

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool with pattern override
    args = CollectionContentArgs(collection="all-docs", pattern="*.txt")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "Text file" in result["value"]
    assert "Markdown" not in result["value"]


async def test_multiple_categories_aggregates_content(tmp_path, monkeypatch):
    """Test that multiple categories aggregate content correctly."""
    import json

    from mcp_guide.models import Category, Collection, Project
    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Create test files in different directories
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    (dir1 / "file1.md").write_text("# Content 1")

    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    (dir2 / "file2.md").write_text("# Content 2")

    # Create test project with multiple categories
    project = Project(
        name="test",
        categories=[
            Category(name="cat1", dir="dir1", patterns=["*.md"]),
            Category(name="cat2", dir="dir2", patterns=["*.md"]),
        ],
        collections=[Collection(name="all-docs", categories=["cat1", "cat2"])],
    )

    # Mock session
    class MockSession:
        async def get_project(self):
            return project

        def get_docroot(self):
            return str(tmp_path)

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool
    args = CollectionContentArgs(collection="all-docs")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "Content 1" in result["value"]
    assert "Content 2" in result["value"]


async def test_tool_handles_file_read_error(tmp_path, monkeypatch):
    """Test that file read errors are handled and include category prefix."""
    import json

    from mcp_guide.models import Category, Collection, Project
    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Create test files
    (tmp_path / "test.md").write_text("# Test Content")

    # Create test project
    project = Project(
        name="test",
        categories=[Category(name="docs", dir=".", patterns=["*.md"])],
        collections=[Collection(name="all-docs", categories=["docs"])],
    )

    # Mock session
    class MockSession:
        async def get_project(self):
            return project

        def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    # Mock read_file_contents to return errors with category prefix
    async def mock_read_file_contents(files, base_dir, category_prefix=None):
        return [f"{category_prefix}/test.md: Permission denied"]

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)
    monkeypatch.setattr("mcp_guide.tools.tool_collection.read_file_contents", mock_read_file_contents)

    # Call tool
    args = CollectionContentArgs(collection="all-docs")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == "file_read_error"
    assert "docs/test.md" in result["error"]


async def test_get_or_create_session_error_returns_no_project_failure(monkeypatch):
    """Test that get_or_create_session ValueError returns no_project error."""
    import json

    from mcp_guide.tools.tool_collection import (
        CollectionContentArgs,
        get_collection_content,
    )

    # Mock get_or_create_session to raise ValueError
    async def mock_get_session(ctx=None):
        raise ValueError("No project configured")

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool
    args = CollectionContentArgs(collection="test-collection")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == "no_project"
    assert "No project configured" in result["error"]
