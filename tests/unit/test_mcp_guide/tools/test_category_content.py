"""Tests for category_content tool."""

import anyio
import pytest
from pydantic import ValidationError


def create_mock_session(project, tmp_path):
    """Create a mock session with required methods."""

    class MockSession:
        def __init__(self):
            pass

        async def get_project(self):
            return project

        async def get_docroot(self):
            return str(tmp_path)

        def project_flags(self):
            class MockFlags:
                async def list(self):
                    return {}

            return MockFlags()

        def feature_flags(self):
            class MockFlags:
                async def list(self):
                    return {}

            return MockFlags()

    return MockSession()


@pytest.mark.parametrize(
    "scenario,expression,pattern,should_raise,expected_expression,expected_pattern",
    [
        ("class_exists", None, None, False, None, None),
        ("category_required", None, None, True, None, None),
        ("pattern_optional", "docs", None, False, "docs", None),
        ("valid_with_pattern", "docs", "*.md", False, "docs", "*.md"),
    ],
)
def test_category_content_args_schema(
    scenario, expression, pattern, should_raise, expected_expression, expected_pattern
):
    """Test CategoryContentArgs schema validation scenarios."""
    from mcp_guide.tools.tool_category import CategoryContentArgs

    if scenario == "class_exists":
        assert CategoryContentArgs is not None
        return

    if should_raise:
        with pytest.raises(ValidationError):
            CategoryContentArgs() if expression is None else CategoryContentArgs(expression=expression, pattern=pattern)
    else:
        args = (
            CategoryContentArgs(expression=expression, pattern=pattern)
            if pattern
            else CategoryContentArgs(expression=expression)
        )
        assert args.expression == expected_expression
        assert args.pattern == expected_pattern


def test_schema_has_field_descriptions():
    """Test that fields have descriptions."""
    from mcp_guide.tools.tool_category import CategoryContentArgs

    schema = CategoryContentArgs.model_json_schema()
    assert "expression" in schema["properties"]
    assert "description" in schema["properties"]["expression"]
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


@pytest.mark.anyio
async def test_category_content_function_exists():
    """Test that category_content function exists."""
    from mcp_guide.tools.tool_category import category_content

    assert category_content is not None
    assert callable(category_content)


@pytest.mark.anyio
async def test_tool_returns_result_ok_on_success(tmp_path, monkeypatch):
    """Test that tool returns Result.ok() with content on success."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        CategoryContentArgs,
        category_content,
    )

    # Create test files
    test_file = tmp_path / "README"
    test_file.write_text("# Test Content")

    # Create test project with category
    project = Project(
        name="test", categories={"docs": Category(dir=".", name="docs", patterns=["README"])}, collections={}
    )

    # Mock get_session
    async def mock_get_session(ctx=None):
        return create_mock_session(project, tmp_path)

    monkeypatch.setattr("mcp_guide.tools.tool_helpers.get_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(expression="docs")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "value" in result
    assert "Test Content" in result["value"]


@pytest.mark.anyio
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

    async def mock_get_session(ctx=None):
        return create_mock_session(project, tmp_path)

    monkeypatch.setattr("mcp_guide.tools.tool_helpers.get_session", mock_get_session)

    # Call tool with non-existent category
    args = CategoryContentArgs(expression="nonexistent")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == ERROR_NOT_FOUND
    assert result["instruction"] == INSTRUCTION_NOTFOUND_ERROR
    assert "nonexistent" in result["error"]


@pytest.mark.anyio
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
    project = Project(
        name="test", categories={"docs": Category(dir=".", name="docs", patterns=["README"])}, collections={}
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(project, tmp_path)

    monkeypatch.setattr("mcp_guide.tools.tool_helpers.get_session", mock_get_session)

    # Test 1: Default patterns - should return success
    args = CategoryContentArgs(expression="docs")
    result_json = await category_content(args)
    result = json.loads(result_json)
    assert result["success"] is True
    assert result["instruction"] == INSTRUCTION_PATTERN_ERROR
    assert "No files found" in result["value"]

    # Test 2: Pattern override - should also return success (consistent with other tools)
    args = CategoryContentArgs(expression="docs", pattern="*.txt")
    result_json = await category_content(args)
    result = json.loads(result_json)
    assert result["success"] is True
    assert result["instruction"] == INSTRUCTION_PATTERN_ERROR
    assert "*.txt" in result["value"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "scenario,patterns,error_map",
    [
        ("single_file", ["README"], {"README": PermissionError("Permission denied")}),
        (
            "multiple_files",
            ["file1", "file2", "file3"],
            {
                "file1": FileNotFoundError("File not found"),
                "file2": PermissionError("Permission denied"),
                "file3": UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte"),
            },
        ),
    ],
    ids=["single_file", "multiple_files"],
)
async def test_file_read_error_scenarios(tmp_path, monkeypatch, scenario, patterns, error_map):
    """Test that file read errors return ERROR_FILE_READ with appropriate aggregation."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        ERROR_FILE_READ,
        INSTRUCTION_FILE_ERROR,
        CategoryContentArgs,
        category_content,
    )

    # Create test project with category
    project = Project(
        name="test", categories={"docs": Category(dir=".", name="docs", patterns=patterns)}, collections={}
    )

    # Create files
    for pattern in patterns:
        (tmp_path / pattern).write_text(f"content-{pattern}")

    async def mock_get_session(ctx=None):
        return create_mock_session(project, tmp_path)

    # Mock read_file_content to raise errors based on error_map (for templates)
    async def mock_read_error(path):
        for filename, error in error_map.items():
            if filename in str(path):
                raise error
        return "content"

    # Mock anyio.Path.read_text to raise errors based on error_map (for non-templates via process_file)

    async def mock_read_text(self, encoding=None):
        for filename, error in error_map.items():
            if filename in str(self):
                raise error
        return "content"

    monkeypatch.setattr("mcp_guide.tools.tool_helpers.get_session", mock_get_session)
    monkeypatch.setattr("mcp_guide.core.file_reader.read_file_content", mock_read_error)
    monkeypatch.setattr(anyio.Path, "read_text", mock_read_text)

    # Call tool
    args = CategoryContentArgs(expression="docs")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == ERROR_FILE_READ
    assert result["instruction"] == INSTRUCTION_FILE_ERROR

    # All files should be in error message
    for filename in error_map.keys():
        assert filename in result["error"]

    # Multiple files should have semicolon aggregation
    if len(error_map) > 1:
        assert ";" in result["error"]


@pytest.mark.anyio
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

    async def mock_get_session(ctx=None):
        return create_mock_session(project, tmp_path)

    monkeypatch.setattr("mcp_guide.tools.tool_helpers.get_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(expression="test")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert "success" in result
    assert "error_type" in result
    assert "instruction" in result
    assert "error" in result
    assert result["success"] is False
