"""Integration tests for collection management tools via MCP client.

Tests collection tools through the MCP protocol interface to verify:
- End-to-end workflows through real client
- Configuration persistence across operations
- Category validation integration
- Error handling through protocol layer
"""

import json
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_guide.models import Category
from mcp_guide.session import get_or_create_session, remove_current_session
from mcp_guide.tools.tool_collection import (
    CollectionAddArgs,
    CollectionListArgs,
    CollectionRemoveArgs,
    CollectionUpdateArgs,
)
from tests.conftest import call_mcp_tool


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
    # Resolve symlinks to avoid path mismatch issues on macOS
    resolved_tmp_path = tmp_path.resolve()
    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(resolved_tmp_path))

    # Setup initial categories
    await session.update_config(
        lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"]))
        .with_category("tests", Category(dir="tests", patterns=["test_*.py"]))
        .with_category("docs", Category(dir="docs", patterns=["*.md"]))
    )

    yield session
    await remove_current_session("test")


# Phase 2: Collection Management Workflow Tests


@pytest.mark.anyio
async def test_add_collection_via_mcp(mcp_server, test_session, monkeypatch):
    """Test adding collection through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionAddArgs(name="backend", categories=["api", "tests"], description="Backend code")
        result = await call_mcp_tool(client, "collection_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True


@pytest.mark.anyio
async def test_list_collections_via_mcp(mcp_server, test_session, monkeypatch):
    """Test listing collections through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add collection
        args1 = CollectionAddArgs(name="backend", categories=["api", "tests"], description="Backend code")
        await call_mcp_tool(client, "collection_add", args1)

        # List collections
        args = CollectionListArgs(verbose=True)
        result = await call_mcp_tool(client, "collection_list", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        collections = response["value"]
        assert len(collections) == 1
        assert collections[0]["name"] == "backend"
        assert collections[0]["categories"] == ["api", "tests"]


@pytest.mark.anyio
async def test_update_collection_via_mcp(mcp_server, test_session, monkeypatch):
    """Test updating collection through MCP client."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add collection
        args1 = CollectionAddArgs(name="backend", categories=["api", "tests"])
        await call_mcp_tool(client, "collection_add", args1)

        # Update collection
        args = CollectionUpdateArgs(name="backend", add_categories=["docs"])
        result = await call_mcp_tool(client, "collection_update", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True

        # Verify update
        args2 = CollectionListArgs(verbose=True)
        result = await call_mcp_tool(client, "collection_list", args2)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        collections = response["value"]
        assert "docs" in collections[0]["categories"]


@pytest.mark.anyio
async def test_remove_collection_via_mcp(mcp_server, test_session, monkeypatch):
    """Test removing collection through MCP client."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add collection
        args1 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args1)

        # Remove collection
        args = CollectionRemoveArgs(name="backend")
        result = await call_mcp_tool(client, "collection_remove", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True

        # Verify removed
        args2 = CollectionListArgs(verbose=True)
        result = await call_mcp_tool(client, "collection_list", args2)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        collections = response["value"]
        assert len(collections) == 0


@pytest.mark.anyio
async def test_collection_management_workflow(mcp_server, test_session, monkeypatch):
    """Test complete collection management workflow through MCP client."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add
        args = CollectionAddArgs(name="backend", categories=["api", "tests"], description="Backend code")
        result = await call_mcp_tool(client, "collection_add", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify added
        args = CollectionListArgs(verbose=True)
        result = await call_mcp_tool(client, "collection_list", args)
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert len(collections) == 1
        assert collections[0]["name"] == "backend"

        # Update - add category
        args = CollectionUpdateArgs(name="backend", add_categories=["docs"])
        result = await call_mcp_tool(client, "collection_update", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify updated
        args = CollectionListArgs(verbose=True)
        result = await call_mcp_tool(client, "collection_list", args)
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert "docs" in collections[0]["categories"]

        # Remove
        args = CollectionRemoveArgs(name="backend")
        result = await call_mcp_tool(client, "collection_remove", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify removed
        args = CollectionListArgs(verbose=True)
        result = await call_mcp_tool(client, "collection_list", args)
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert len(collections) == 0


# Phase 3: Category Validation Integration Tests


@pytest.mark.anyio
async def test_add_collection_invalid_category_fails(mcp_server, test_session, monkeypatch):
    """Test adding collection with invalid category fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionAddArgs(name="backend", categories=["nonexistent"])
        result = await call_mcp_tool(client, "collection_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "nonexistent" in response["error"].lower() or "invalid" in response["error"].lower()


@pytest.mark.anyio
async def test_update_collection_invalid_category_fails(mcp_server, test_session, monkeypatch):
    """Test updating collection with invalid category fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add valid collection
        args1 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args1)

        # Try to update with invalid category
        args = CollectionUpdateArgs(name="backend", add_categories=["nonexistent"])
        result = await call_mcp_tool(client, "collection_update", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "nonexistent" in response["error"].lower() or "invalid" in response["error"].lower()


@pytest.mark.anyio
async def test_validation_errors_return_proper_format(mcp_server, test_session, monkeypatch):
    """Test validation errors return proper Result format."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionAddArgs(name="backend", categories=["nonexistent"])
        result = await call_mcp_tool(client, "collection_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        # Verify Result format
        assert "success" in response
        assert "error" in response
        assert response["success"] is False
        assert isinstance(response["error"], str)
        assert len(response["error"]) > 0


# Phase 4: Configuration Persistence Tests


@pytest.mark.anyio
async def test_collection_persists_after_add(mcp_server, tmp_path, monkeypatch):
    """Test collection persists after add."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add collection
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args)

    await remove_current_session("test")

    # Reload session and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    await remove_current_session("test")


@pytest.mark.anyio
async def test_collection_persists_after_update(mcp_server, tmp_path, monkeypatch):
    """Test collection persists after update."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(
        lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])).with_category(
            "docs", Category(dir="docs", patterns=["*.md"])
        )
    )

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args1)
        args2 = CollectionUpdateArgs(name="backend", add_categories=["docs"])
        await call_mcp_tool(client, "collection_update", args2)

    await remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    assert "docs" in project.collections["backend"].categories
    await remove_current_session("test")


@pytest.mark.anyio
async def test_collection_removed_persists(mcp_server, tmp_path, monkeypatch):
    """Test collection removal persists."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add collection
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args1)
        args2 = CollectionRemoveArgs(name="backend")
        await call_mcp_tool(client, "collection_remove", args2)

    await remove_current_session("test")

    # Reload and verify removed
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 0
    await remove_current_session("test")


@pytest.mark.anyio
async def test_multiple_operations_persist(mcp_server, tmp_path, monkeypatch):
    """Test multiple operations persist correctly."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(
        lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])).with_category(
            "docs", Category(dir="docs", patterns=["*.md"])
        )
    )

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args1)
        args2 = CollectionAddArgs(name="frontend", categories=["docs"])
        await call_mcp_tool(client, "collection_add", args2)
        args3 = CollectionUpdateArgs(name="backend", add_categories=["docs"])
        await call_mcp_tool(client, "collection_update", args3)
        args4 = CollectionRemoveArgs(name="frontend")
        await call_mcp_tool(client, "collection_remove", args4)

    await remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    assert set(project.collections["backend"].categories) == {"api", "docs"}
    await remove_current_session("test")


# Phase 5: Error Cases Tests


@pytest.mark.anyio
async def test_add_duplicate_collection_fails(mcp_server, test_session, monkeypatch):
    """Test adding duplicate collection fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args1)

        # Try to add duplicate
        args2 = CollectionAddArgs(name="backend", categories=["api"])
        result = await call_mcp_tool(client, "collection_add", args2)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "backend" in response["error"].lower() or "exists" in response["error"].lower()


@pytest.mark.anyio
async def test_remove_nonexistent_collection_fails(mcp_server, test_session, monkeypatch):
    """Test removing non-existent collection fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionRemoveArgs(name="nonexistent")
        result = await call_mcp_tool(client, "collection_remove", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False


@pytest.mark.anyio
async def test_update_nonexistent_collection_fails(mcp_server, test_session, monkeypatch):
    """Test updating non-existent collection fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionUpdateArgs(name="nonexistent", add_categories=["api"])
        result = await call_mcp_tool(client, "collection_update", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False


@pytest.mark.anyio
async def test_add_collection_invalid_name_fails(mcp_server, test_session, monkeypatch):
    """Test adding collection with invalid name fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionAddArgs(name="invalid name!", categories=["api"])
        result = await call_mcp_tool(client, "collection_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False


@pytest.mark.anyio
async def test_add_collection_empty_categories(mcp_server, test_session, monkeypatch):
    """Test adding collection with empty categories succeeds."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CollectionAddArgs(name="empty", categories=[])
        result = await call_mcp_tool(client, "collection_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True


# Phase 6: Multi-Tool Workflows


@pytest.mark.anyio
async def test_collection_removal_preserves_categories(mcp_server, tmp_path, monkeypatch):
    """Test removing collection preserves categories."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args1)
        args2 = CollectionRemoveArgs(name="backend")
        await call_mcp_tool(client, "collection_remove", args2)

    await remove_current_session("test")

    # Reload and verify categories still exist
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 0
    assert len(project.categories) == 1
    assert "api" in project.categories
    await remove_current_session("test")


# Collection content functionality is now handled by the unified get_content tool
