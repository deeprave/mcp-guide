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

from mcp_guide.session import get_or_create_session, remove_current_session


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server():
    """Create fresh MCP server for this test module."""
    import sys
    from importlib import reload

    from mcp_guide.server import _ToolsProxy, create_server

    # Reset proxy to clear any previously registered tools
    _ToolsProxy._instance = None

    # Create new server instance
    server = create_server()

    # Reload tool modules to re-execute decorators with new server
    if "mcp_guide.tools.tool_category" in sys.modules:
        reload(sys.modules["mcp_guide.tools.tool_category"])
    if "mcp_guide.tools.tool_collection" in sys.modules:
        reload(sys.modules["mcp_guide.tools.tool_collection"])

    yield server

    # Clean up after module
    _ToolsProxy._instance = None


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
