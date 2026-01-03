"""Tests for category_content tool."""


def test_category_content_args_exists():
    """Test that CategoryContentArgs class exists."""
    from mcp_guide.tools.tool_category import CategoryContentArgs

    assert CategoryContentArgs is not None


def test_category_field_is_required():
    """Test that category field is required."""
    import pytest
    from pydantic import ValidationError

    from mcp_guide.tools.tool_category import CategoryContentArgs

    with pytest.raises(ValidationError):
        CategoryContentArgs()


def test_pattern_field_is_optional():
    """Test that pattern field is optional."""
    from mcp_guide.tools.tool_category import CategoryContentArgs

    args = CategoryContentArgs(category="docs")
    assert args.category == "docs"
    assert args.pattern is None


def test_schema_validates_correctly():
    """Test that schema validates with valid data."""
    from mcp_guide.tools.tool_category import CategoryContentArgs

    args = CategoryContentArgs(category="docs", pattern="*.md")
    assert args.category == "docs"
    assert args.pattern == "*.md"


def test_schema_has_field_descriptions():
    """Test that fields have descriptions."""
    from mcp_guide.tools.tool_category import CategoryContentArgs

    schema = CategoryContentArgs.model_json_schema()
    assert "category" in schema["properties"]
    assert "description" in schema["properties"]["category"]
    assert "pattern" in schema["properties"]
    assert "description" in schema["properties"]["pattern"]


def test_error_types_defined():
    """Test that error types are defined."""
    from mcp_guide.tools.tool_category import ERROR_NOT_FOUND

    assert ERROR_NOT_FOUND == "not_found"


def test_error_instructions_defined():
    """Test that error instructions are defined."""
    from mcp_guide.result_constants import (
        INSTRUCTION_NOTFOUND_ERROR as CONST_NOTFOUND_ERROR,
    )
    from mcp_guide.result_constants import (
        INSTRUCTION_PATTERN_ERROR as CONST_PATTERN_ERROR,
    )
    from mcp_guide.tools.tool_category import (
        INSTRUCTION_NOTFOUND_ERROR,
        INSTRUCTION_PATTERN_ERROR,
    )

    assert INSTRUCTION_NOTFOUND_ERROR == CONST_NOTFOUND_ERROR
    assert INSTRUCTION_PATTERN_ERROR == CONST_PATTERN_ERROR


def test_instructions_prevent_futile_remediation():
    """Test that instructions explicitly prevent agent remediation."""
    from mcp_guide.tools.tool_category import (
        INSTRUCTION_NOTFOUND_ERROR,
        INSTRUCTION_PATTERN_ERROR,
    )

    # Both should tell agent not to try fixing
    assert any(phrase in INSTRUCTION_NOTFOUND_ERROR.lower() for phrase in ["no further action", "do not", "don't"])
    assert any(
        phrase in INSTRUCTION_PATTERN_ERROR.lower()
        for phrase in ["do not attempt", "don't attempt", "no further action"]
    )


async def test_category_content_function_exists():
    """Test that category_content function exists."""
    from mcp_guide.tools.tool_category import category_content

    assert category_content is not None
    assert callable(category_content)


async def test_tool_returns_result_ok_on_success(tmp_path, monkeypatch):
    """Test that tool returns Result.ok() with content on success."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        CategoryContentArgs,
        category_content,
    )

    # Create test files
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test Content")

    # Create test project with category
    project = Project(name="test", categories={"docs": Category(dir=".", patterns=["*.md"])}, collections={})

    # Mock session

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(category="docs")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "value" in result
    assert "Test Content" in result["value"]


async def test_tool_formats_with_active_formatter(tmp_path, monkeypatch):
    """Test that tool uses active formatter."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        CategoryContentArgs,
        category_content,
    )
    from mcp_guide.utils.formatter_selection import set_formatter

    # Create test files
    test_file = tmp_path / "test.md"
    test_file.write_text("Test")

    # Create test project
    project = Project(name="test", categories={"docs": Category(dir=".", patterns=["*.md"])}, collections={})

    # Mock session

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Test with MIME formatter
    set_formatter("mime")
    args = CategoryContentArgs(category="docs")
    result_json = await category_content(args)
    result = json.loads(result_json)

    # MIME format should have headers
    assert "Content-Type:" in result["value"]

    # Reset to plain
    set_formatter("plain")


async def test_category_not_found_returns_failure(tmp_path, monkeypatch):
    """Test that category not found returns Result.failure()."""
    import json

    from mcp_guide.models import Project
    from mcp_guide.tools.tool_category import (
        ERROR_NOT_FOUND,
        INSTRUCTION_NOTFOUND_ERROR,
        CategoryContentArgs,
        category_content,
    )

    # Create test project with no categories
    project = Project(name="test", categories={}, collections={})

    # Mock session

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool with non-existent category
    args = CategoryContentArgs(category="nonexistent")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == ERROR_NOT_FOUND
    assert result["instruction"] == INSTRUCTION_NOTFOUND_ERROR
    assert "nonexistent" in result["error"]


async def test_no_matches_returns_failure(tmp_path, monkeypatch):
    """Test that no matches with default patterns returns success, with pattern override returns failure."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        INSTRUCTION_PATTERN_ERROR,
        CategoryContentArgs,
        category_content,
    )

    # Create test project with category but no matching files
    project = Project(name="test", categories={"docs": Category(dir=".", patterns=["*.md"])}, collections={})

    # Mock session (no files created in tmp_path)

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Test 1: Default patterns - should return success
    args = CategoryContentArgs(category="docs")
    result_json = await category_content(args)
    result = json.loads(result_json)
    assert result["success"] is True
    assert result["instruction"] == INSTRUCTION_PATTERN_ERROR
    assert "No files found" in result["value"]

    # Test 2: Pattern override - should also return success (consistent with other tools)
    args = CategoryContentArgs(category="docs", pattern="*.txt")
    result_json = await category_content(args)
    result = json.loads(result_json)
    assert result["success"] is True
    assert result["instruction"] == INSTRUCTION_PATTERN_ERROR
    assert "*.txt" in result["value"]


async def test_file_read_error_single_file(tmp_path, monkeypatch):
    """Test that single file read error returns ERROR_FILE_READ."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        ERROR_FILE_READ,
        INSTRUCTION_FILE_ERROR,
        CategoryContentArgs,
        category_content,
    )

    # Create test project with category
    project = Project(name="test", categories={"docs": Category(dir=".", patterns=["*.md"])}, collections={})

    # Create a file
    test_file = tmp_path / "test.md"
    test_file.write_text("content")

    # Mock session

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    # Mock read_file_content to raise error
    async def mock_read_error(path):
        raise PermissionError("Permission denied")

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)
    monkeypatch.setattr("mcp_guide.utils.content_utils.read_file_content", mock_read_error)

    # Call tool
    args = CategoryContentArgs(category="docs")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == ERROR_FILE_READ
    assert result["instruction"] == INSTRUCTION_FILE_ERROR
    assert "test.md" in result["error"]
    assert "Permission denied" in result["error"]


async def test_file_read_error_multiple_files(tmp_path, monkeypatch):
    """Test that multiple file read errors are aggregated."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        ERROR_FILE_READ,
        INSTRUCTION_FILE_ERROR,
        CategoryContentArgs,
        category_content,
    )

    # Create test project with category
    project = Project(name="test", categories={"docs": Category(dir=".", patterns=["*.md"])}, collections={})

    # Create multiple files
    (tmp_path / "file1.md").write_text("content1")
    (tmp_path / "file2.md").write_text("content2")
    (tmp_path / "file3.md").write_text("content3")

    # Mock session

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    # Mock read_file_content to raise different errors for different files
    call_count = 0

    async def mock_read_error(path):
        nonlocal call_count
        call_count += 1
        if "file1" in str(path):
            raise FileNotFoundError("File not found")
        elif "file2" in str(path):
            raise PermissionError("Permission denied")
        else:
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)
    monkeypatch.setattr("mcp_guide.utils.content_utils.read_file_content", mock_read_error)

    # Call tool
    args = CategoryContentArgs(category="docs")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == ERROR_FILE_READ
    assert result["instruction"] == INSTRUCTION_FILE_ERROR
    # All three files should be in error message
    assert "file1.md" in result["error"]
    assert "file2.md" in result["error"]
    assert "file3.md" in result["error"]
    # Check aggregation format with semicolons
    assert ";" in result["error"]


async def test_error_responses_include_all_fields(tmp_path, monkeypatch):
    """Test that error responses include error_type, instruction, and message."""
    import json

    from mcp_guide.models import Project
    from mcp_guide.tools.tool_category import (
        CategoryContentArgs,
        category_content,
    )

    # Create test project with no categories
    project = Project(name="test", categories={}, collections={})

    # Mock session

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(category="test")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert "success" in result
    assert "error_type" in result
    assert "instruction" in result
    assert "error" in result
    assert result["success"] is False
