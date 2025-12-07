"""Integration tests for category management tools via MCP client.

Tests category tools through the MCP protocol interface to verify:
- End-to-end workflows through real client
- Configuration persistence across operations
- Validation integration
- Error handling through protocol layer
"""

import json
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_guide.models import Category
from mcp_guide.session import get_or_create_session, remove_current_session


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_category", "tool_collection"])


@pytest.fixture
async def test_session(tmp_path: Path):
    """Create test session with isolated config."""
    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    yield session
    remove_current_session("test")


# Basic CRUD Operations


@pytest.mark.anyio
async def test_add_category_via_mcp(mcp_server, test_session, monkeypatch):
    """Test adding category through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "api" in response["value"]


@pytest.mark.anyio
async def test_list_categories_via_mcp(mcp_server, test_session, monkeypatch):
    """Test listing categories through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        await client.call_tool("category_add", {"name": "docs", "dir": "docs", "patterns": ["*.md"]})

        result = await client.call_tool("category_list", {"verbose": False})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert len(response["value"]) == 2
        assert "api" in response["value"]
        assert "docs" in response["value"]


@pytest.mark.anyio
async def test_update_category_via_mcp(mcp_server, test_session, monkeypatch):
    """Test updating category through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})

        result = await client.call_tool("category_update", {"name": "api", "add_patterns": ["*.pyi"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "api" in response["value"]


@pytest.mark.anyio
async def test_remove_category_via_mcp(mcp_server, test_session, monkeypatch):
    """Test removing category through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})

        result = await client.call_tool("category_remove", {"name": "api"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "api" in response["value"]


# Workflow Tests


@pytest.mark.anyio
async def test_category_management_workflow(mcp_server, test_session, monkeypatch):
    """Test complete category management workflow."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add category
        result = await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # Update category
        result = await client.call_tool("category_update", {"name": "api", "add_patterns": ["*.pyi"]})
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List categories
        result = await client.call_tool("category_list", {"verbose": True})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True
        assert len(response["value"]) == 1
        assert response["value"][0]["name"] == "api"
        assert "*.pyi" in response["value"][0]["patterns"]

        # Remove category
        result = await client.call_tool("category_remove", {"name": "api"})
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # Verify removal
        result = await client.call_tool("category_list", {"verbose": True})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert len(response["value"]) == 0


# Validation Tests


@pytest.mark.anyio
async def test_add_category_invalid_name_fails(mcp_server, test_session, monkeypatch):
    """Test adding category with invalid name fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("category_add", {"name": "", "dir": "src/api", "patterns": ["*.py"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_add_category_invalid_patterns_fails(mcp_server, test_session, monkeypatch):
    """Test adding category with invalid patterns fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Use pattern with path traversal
        result = await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["../*.py"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_add_category_duplicate_fails(mcp_server, test_session, monkeypatch):
    """Test adding duplicate category fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})

        result = await client.call_tool("category_add", {"name": "api", "dir": "src/api2", "patterns": ["*.py"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_update_nonexistent_category_fails(mcp_server, test_session, monkeypatch):
    """Test updating non-existent category fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("category_update", {"name": "nonexistent", "add_patterns": ["*.py"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_remove_nonexistent_category_fails(mcp_server, test_session, monkeypatch):
    """Test removing non-existent category fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("category_remove", {"name": "nonexistent"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


# Persistence Tests


@pytest.mark.anyio
async def test_category_persists_after_add(mcp_server, tmp_path, monkeypatch):
    """Test category persists after add."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add category
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})

    remove_current_session("test")

    # Reload session and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert project.categories[0].name == "api"
    assert project.categories[0].dir == "src/api"
    assert "*.py" in project.categories[0].patterns

    remove_current_session("test")


@pytest.mark.anyio
async def test_category_persists_after_update(mcp_server, tmp_path, monkeypatch):
    """Test category persists after update."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add/update category
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        await client.call_tool("category_update", {"name": "api", "add_patterns": ["*.pyi"]})

    remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert project.categories[0].name == "api"
    assert "*.pyi" in project.categories[0].patterns

    remove_current_session("test")


@pytest.mark.anyio
async def test_category_removed_persists(mcp_server, tmp_path, monkeypatch):
    """Test category removal persists."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add/remove category
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        await client.call_tool("category_remove", {"name": "api"})

    remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 0

    remove_current_session("test")


@pytest.mark.anyio
async def test_multiple_operations_persist(mcp_server, tmp_path, monkeypatch):
    """Test multiple operations persist correctly."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with multiple operations
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        await client.call_tool("category_add", {"name": "docs", "dir": "docs", "patterns": ["*.md"]})
        await client.call_tool("category_update", {"name": "api", "add_patterns": ["*.pyi"]})
        await client.call_tool("category_remove", {"name": "docs"})

    remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert project.categories[0].name == "api"
    assert "*.pyi" in project.categories[0].patterns

    remove_current_session("test")


# Integration Tests


@pytest.mark.anyio
async def test_category_removal_preserves_collections(mcp_server, tmp_path, monkeypatch):
    """Test removing category updates collections by removing the category reference."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        await client.call_tool("category_add", {"name": "docs", "dir": "docs", "patterns": ["*.md"]})
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api", "docs"]})

        # Remove one category
        await client.call_tool("category_remove", {"name": "api"})

    remove_current_session("test")

    # Reload and verify collection still exists but category reference is removed
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    assert project.collections[0].name == "backend"
    assert "api" not in project.collections[0].categories  # Category reference removed
    assert "docs" in project.collections[0].categories  # Other category remains

    remove_current_session("test")


@pytest.mark.anyio
async def test_update_category_preserves_collections(mcp_server, tmp_path, monkeypatch):
    """Test updating category preserves collections."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("category_add", {"name": "api", "dir": "src/api", "patterns": ["*.py"]})
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})

        # Update category
        await client.call_tool("category_update", {"name": "api", "add_patterns": ["*.pyi"]})

    remove_current_session("test")

    # Reload and verify both category and collection
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert "*.pyi" in project.categories[0].patterns
    assert len(project.collections) == 1
    assert project.collections[0].name == "backend"
    assert "api" in project.collections[0].categories

    remove_current_session("test")


# Phase 7: Category Content Retrieval


@pytest.mark.anyio
async def test_get_category_content_not_found(mcp_server, tmp_path, monkeypatch):
    """Test error when category doesn't exist."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_category_content", {"category": "nonexistent"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "not_found"
        assert "nonexistent" in response["error"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_category_content_empty_category(mcp_server, tmp_path, monkeypatch):
    """Test success message when category has no matching files."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern that won't match any files
    await session.update_config(lambda p: p.with_category(Category(name="guide", dir="guide", patterns=["nomatch*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_category_content", {"category": "guide"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "no files found" in response["value"].lower() or "no matching content" in response["value"].lower()

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_category_content_success_single_file(mcp_server, tmp_path, monkeypatch):
    """Test successful content retrieval with single file."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern matching single file
    await session.update_config(lambda p: p.with_category(Category(name="lang", dir="lang", patterns=["python*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_category_content", {"category": "lang"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Python Guide" in response["value"]
        assert "Java Guide" not in response["value"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_category_content_success_multiple_files(mcp_server, tmp_path, monkeypatch):
    """Test successful content retrieval with multiple files."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern matching multiple files
    await session.update_config(lambda p: p.with_category(Category(name="context", dir="context", patterns=["jira*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_category_content", {"category": "context"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Jira Integration" in response["value"]
        assert "jira:" in response["value"]  # From jira-settings.yaml
        assert "Development Standards" not in response["value"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_category_content_pattern_override(mcp_server, tmp_path, monkeypatch):
    """Test pattern overrides category defaults."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern matching all files
    await session.update_config(lambda p: p.with_category(Category(name="guide", dir="guide", patterns=["*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Request only files matching "guidelines-*"
        result = await client.call_tool("get_category_content", {"category": "guide", "pattern": "guidelines-*"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Feature 1 Guidelines" in response["value"]
        assert "Project Guidelines" not in response["value"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_category_content_file_read_error(mcp_server, tmp_path, monkeypatch):
    """Test error handling when file cannot be read."""
    import os

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category
    await session.update_config(lambda p: p.with_category(Category(name="docs", dir="docs", patterns=["*.md"])))

    # Create test file and make it unreadable
    docroot = Path(tmp_path.resolve()) / "docs" / "docs"
    docroot.mkdir(parents=True, exist_ok=True)
    test_file = docroot / "test.md"
    test_file.write_text("# Test Content")
    os.chmod(test_file, 0o000)

    try:
        async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
            result = await client.call_tool("get_category_content", {"category": "docs"})
            response = json.loads(result.content[0].text)  # type: ignore[union-attr]

            assert response["success"] is False
            assert response["error_type"] == "file_read_error"
            assert "test.md" in response["error"]
    finally:
        # Restore permissions for cleanup
        os.chmod(test_file, 0o644)

    remove_current_session("test")
