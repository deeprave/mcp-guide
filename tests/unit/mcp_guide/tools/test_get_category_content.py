"""Tests for get_category_content tool."""


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
    from mcp_guide.tools.tool_category import ERROR_NO_MATCHES, ERROR_NOT_FOUND

    assert ERROR_NOT_FOUND == "not_found"
    assert ERROR_NO_MATCHES == "no_matches"


def test_error_instructions_defined():
    """Test that error instructions are defined."""
    from mcp_guide.tools.tool_category import (
        INSTRUCTION_NO_MATCHES,
        INSTRUCTION_NOT_FOUND,
    )

    assert "Present this error to the user" in INSTRUCTION_NOT_FOUND
    assert "take no further action" in INSTRUCTION_NOT_FOUND
    assert "Present this error to the user" in INSTRUCTION_NO_MATCHES
    assert "Do NOT attempt corrective action" in INSTRUCTION_NO_MATCHES


def test_instructions_prevent_futile_remediation():
    """Test that instructions explicitly prevent agent remediation."""
    from mcp_guide.tools.tool_category import (
        INSTRUCTION_NO_MATCHES,
        INSTRUCTION_NOT_FOUND,
    )

    # Both should tell agent not to try fixing
    assert any(phrase in INSTRUCTION_NOT_FOUND.lower() for phrase in ["no further action", "do not", "don't"])
    assert any(
        phrase in INSTRUCTION_NO_MATCHES.lower() for phrase in ["do not attempt", "don't attempt", "no further action"]
    )


async def test_get_category_content_function_exists():
    """Test that get_category_content function exists."""
    from mcp_guide.tools.tool_category import get_category_content

    assert get_category_content is not None
    assert callable(get_category_content)


async def test_tool_returns_result_ok_on_success(tmp_path, monkeypatch):
    """Test that tool returns Result.ok() with content on success."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        CategoryContentArgs,
        get_category_content,
    )

    # Create test files
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test Content")

    # Create test project with category
    project = Project(
        name="test",
        categories=[Category(name="docs", dir=".", patterns=["*.md"])],
    )

    # Mock session
    class MockConfigManager:
        def get_docroot(self):
            return str(tmp_path)

    class MockSession:
        def __init__(self):
            self.config_manager = MockConfigManager()

        async def get_project(self):
            return project

    # Mock get_or_create_session
    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(category="docs")
    result_json = await get_category_content(args)

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
        get_category_content,
    )
    from mcp_guide.utils.formatter_selection import set_formatter

    # Create test files
    test_file = tmp_path / "test.md"
    test_file.write_text("Test")

    # Create test project
    project = Project(
        name="test",
        categories=[Category(name="docs", dir=".", patterns=["*.md"])],
    )

    # Mock session
    class MockConfigManager:
        def get_docroot(self):
            return str(tmp_path)

    class MockSession:
        def __init__(self):
            self.config_manager = MockConfigManager()

        async def get_project(self):
            return project

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Test with MIME formatter
    set_formatter("mime")
    args = CategoryContentArgs(category="docs")
    result_json = await get_category_content(args)
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
        INSTRUCTION_NOT_FOUND,
        CategoryContentArgs,
        get_category_content,
    )

    # Create test project with no categories
    project = Project(name="test", categories=[])

    # Mock session
    class MockConfigManager:
        def get_docroot(self):
            return str(tmp_path)

    class MockSession:
        def __init__(self):
            self.config_manager = MockConfigManager()

        async def get_project(self):
            return project

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool with non-existent category
    args = CategoryContentArgs(category="nonexistent")
    result_json = await get_category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == ERROR_NOT_FOUND
    assert result["instruction"] == INSTRUCTION_NOT_FOUND
    assert "nonexistent" in result["error"]


async def test_no_matches_returns_failure(tmp_path, monkeypatch):
    """Test that no matches returns Result.failure()."""
    import json

    from mcp_guide.models import Category, Project
    from mcp_guide.tools.tool_category import (
        ERROR_NO_MATCHES,
        INSTRUCTION_NO_MATCHES,
        CategoryContentArgs,
        get_category_content,
    )

    # Create test project with category but no matching files
    project = Project(
        name="test",
        categories=[Category(name="docs", dir=".", patterns=["*.md"])],
    )

    # Mock session (no files created in tmp_path)
    class MockConfigManager:
        def get_docroot(self):
            return str(tmp_path)

    class MockSession:
        def __init__(self):
            self.config_manager = MockConfigManager()

        async def get_project(self):
            return project

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(category="docs")
    result_json = await get_category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is False
    assert result["error_type"] == ERROR_NO_MATCHES
    assert result["instruction"] == INSTRUCTION_NO_MATCHES
    assert "docs" in result["error"]


async def test_error_responses_include_all_fields(tmp_path, monkeypatch):
    """Test that error responses include error_type, instruction, and message."""
    import json

    from mcp_guide.models import Project
    from mcp_guide.tools.tool_category import (
        CategoryContentArgs,
        get_category_content,
    )

    # Create test project with no categories
    project = Project(name="test", categories=[])

    # Mock session
    class MockConfigManager:
        def get_docroot(self):
            return str(tmp_path)

    class MockSession:
        def __init__(self):
            self.config_manager = MockConfigManager()

        async def get_project(self):
            return project

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(category="test")
    result_json = await get_category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert "success" in result
    assert "error_type" in result
    assert "instruction" in result
    assert "error" in result
    assert result["success"] is False
