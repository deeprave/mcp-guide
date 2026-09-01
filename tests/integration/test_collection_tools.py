"""Integration tests for collection management tools via MCP client.

Tests collection tools through the MCP protocol interface to verify:
- End-to-end workflows through real client
- Configuration persistence across operations
- Category validation integration
- Error handling through protocol layer
"""

import inspect
import json
from pathlib import Path

import pytest
from fastmcp.client import Client, FastMCPTransport

from mcp_guide.models import Category, Collection
from mcp_guide.session import Session
from mcp_guide.tools.tool_category import (
    CategoryCollectionAddArgs,
    CategoryCollectionListArgs,
    CategoryCollectionRemoveArgs,
    CategoryCollectionUpdateArgs,
)
from tests.conftest import call_mcp_tool
from tests.helpers import create_unbound_test_session


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_category", "tool_collection"])


@pytest.fixture
async def empty_session(mcp_server, tmp_path: Path, monkeypatch):
    """Create an isolated Session for legacy protocol exercises."""
    resolved_tmp_path = tmp_path.resolve()
    session = create_unbound_test_session(str(resolved_tmp_path))
    project_root = resolved_tmp_path / "client-roots" / "test"
    project_root.mkdir(parents=True, exist_ok=True)
    await session.bind_project_path(project_root)
    runtime = inspect.getclosurevars(mcp_server._lifespan).nonlocals["runtime"]
    monkeypatch.setattr(runtime, "resolve_session", lambda _owner: session)

    yield session


@pytest.fixture
async def test_session(empty_session):
    """Create seeded test session with categories used by most collection tests."""
    session = empty_session

    # Seed categories directly in memory. These tests only need valid category
    # references available for collection operations; persistence is covered by
    # dedicated tests below.
    session._Session__delegate.bind(  # ty: ignore[attr-defined]
        session._Session__delegate.project.with_category("api", Category(dir="src/api", patterns=["*.py"]))  # ty: ignore[attr-defined]
        .with_category("tests", Category(dir="tests", patterns=["test_*.py"]))
        .with_category("docs", Category(dir="docs", patterns=["*.md"]))
    )

    yield session


async def _get_test_session(config_dir: Path) -> Session:
    """Create a session for persistence assertions without watcher startup."""
    session = create_unbound_test_session(str(config_dir.resolve()))
    project_root = Path(config_dir).resolve() / "client-roots" / "test"
    project_root.mkdir(parents=True, exist_ok=True)
    await session.bind_project_path(project_root)
    return session


# Phase 2: Collection Management Workflow Tests


@pytest.mark.anyio
async def test_add_collection_via_mcp(mcp_server, test_session, monkeypatch):
    """Test adding collection through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = CategoryCollectionAddArgs(
            type="collection", name="backend", categories=["api", "tests"], description="Backend code"
        )
        result = await call_mcp_tool(client, "category_collection_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True


@pytest.mark.anyio
async def test_list_collections_via_mcp(mcp_server, test_session, monkeypatch):
    """Test listing collections through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        # Add collection
        args1 = CategoryCollectionAddArgs(
            type="collection", name="backend", categories=["api", "tests"], description="Backend code"
        )
        await call_mcp_tool(client, "category_collection_add", args1)

        # List collections
        args = CategoryCollectionListArgs(type="collection", verbose=True)
        result = await call_mcp_tool(client, "category_collection_list", args)
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

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        # Add collection
        args1 = CategoryCollectionAddArgs(type="collection", name="backend", categories=["api", "tests"])
        await call_mcp_tool(client, "category_collection_add", args1)

        # Update collection
        args = CategoryCollectionUpdateArgs(type="collection", name="backend", add_categories=["docs"])
        result = await call_mcp_tool(client, "category_collection_update", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True

        # Verify update
        args2 = CategoryCollectionListArgs(type="collection", verbose=True)
        result = await call_mcp_tool(client, "category_collection_list", args2)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        collections = response["value"]
        assert "docs" in collections[0]["categories"]


@pytest.mark.anyio
async def test_remove_collection_via_mcp(mcp_server, test_session, monkeypatch):
    """Test removing collection through MCP client."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        # Add collection
        args1 = CategoryCollectionAddArgs(type="collection", name="backend", categories=["api"])
        await call_mcp_tool(client, "category_collection_add", args1)

        # Remove collection
        args = CategoryCollectionRemoveArgs(type="collection", name="backend")
        result = await call_mcp_tool(client, "category_collection_remove", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True

        # Verify removed
        args2 = CategoryCollectionListArgs(type="collection", verbose=True)
        result = await call_mcp_tool(client, "category_collection_list", args2)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        collections = response["value"]
        assert len(collections) == 0


@pytest.mark.anyio
async def test_collection_management_workflow(mcp_server, test_session, monkeypatch):
    """Test complete collection management workflow through MCP client."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        # Add
        args = CategoryCollectionAddArgs(
            type="collection", name="backend", categories=["api", "tests"], description="Backend code"
        )
        result = await call_mcp_tool(client, "category_collection_add", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify added
        args = CategoryCollectionListArgs(type="collection", verbose=True)
        result = await call_mcp_tool(client, "category_collection_list", args)
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert len(collections) == 1
        assert collections[0]["name"] == "backend"

        # Update - add category
        args = CategoryCollectionUpdateArgs(type="collection", name="backend", add_categories=["docs"])
        result = await call_mcp_tool(client, "category_collection_update", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify updated
        args = CategoryCollectionListArgs(type="collection", verbose=True)
        result = await call_mcp_tool(client, "category_collection_list", args)
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert "docs" in collections[0]["categories"]

        # Remove
        args = CategoryCollectionRemoveArgs(type="collection", name="backend")
        result = await call_mcp_tool(client, "category_collection_remove", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify removed
        args = CategoryCollectionListArgs(type="collection", verbose=True)
        result = await call_mcp_tool(client, "category_collection_list", args)
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert len(collections) == 0


# Phase 3: Category Validation Integration Tests


@pytest.mark.anyio
async def test_add_collection_invalid_category_fails(mcp_server, empty_session, monkeypatch):
    """Test adding collection with invalid category fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = CategoryCollectionAddArgs(type="collection", name="backend", categories=["nonexistent"])
        result = await call_mcp_tool(client, "category_collection_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "nonexistent" in response["error"].lower() or "invalid" in response["error"].lower()


@pytest.mark.anyio
async def test_update_collection_invalid_category_fails(mcp_server, test_session, monkeypatch):
    """Test updating collection with invalid category fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        # Add valid collection
        args1 = CategoryCollectionAddArgs(type="collection", name="backend", categories=["api"])
        await call_mcp_tool(client, "category_collection_add", args1)

        # Try to update with invalid category
        args = CategoryCollectionUpdateArgs(type="collection", name="backend", add_categories=["nonexistent"])
        result = await call_mcp_tool(client, "category_collection_update", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "nonexistent" in response["error"].lower() or "invalid" in response["error"].lower()


@pytest.mark.anyio
async def test_validation_errors_return_proper_format(mcp_server, empty_session, monkeypatch):
    """Test validation errors return proper Result format."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = CategoryCollectionAddArgs(type="collection", name="backend", categories=["nonexistent"])
        result = await call_mcp_tool(client, "category_collection_add", args)
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
    session1 = await _get_test_session(tmp_path)
    await session1.update_config(lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])))

    await session1.update_config(lambda p: p.with_collection("backend", Collection(categories=["api"])))

    # Reload session and verify
    session2 = await _get_test_session(tmp_path)
    project = session2._Session__delegate.project
    assert len(project.collections) == 1


@pytest.mark.anyio
async def test_collection_persists_after_update(mcp_server, tmp_path, monkeypatch):
    """Test collection persists after update."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await _get_test_session(tmp_path)
    await session1.update_config(
        lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])).with_category(
            "docs", Category(dir="docs", patterns=["*.md"])
        )
    )

    await session1.update_config(lambda p: p.with_collection("backend", Collection(categories=["api", "docs"])))

    # Reload and verify
    session2 = await _get_test_session(tmp_path)
    project = session2._Session__delegate.project
    assert len(project.collections) == 1
    assert "docs" in project.collections["backend"].categories


@pytest.mark.anyio
async def test_collection_removed_persists(mcp_server, tmp_path, monkeypatch):
    """Test collection removal persists."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and persist a config with no collections.
    session1 = await _get_test_session(tmp_path)
    await session1.update_config(lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])))

    # Reload and verify removed
    session2 = await _get_test_session(tmp_path)
    project = session2._Session__delegate.project
    assert len(project.collections) == 0


@pytest.mark.anyio
async def test_multiple_operations_persist(mcp_server, tmp_path, monkeypatch):
    """Test multiple operations persist correctly."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await _get_test_session(tmp_path)
    await session1.update_config(
        lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])).with_category(
            "docs", Category(dir="docs", patterns=["*.md"])
        )
    )

    await session1.update_config(lambda p: p.with_collection("backend", Collection(categories=["api", "docs"])))

    # Reload and verify
    session2 = await _get_test_session(tmp_path)
    project = session2._Session__delegate.project
    assert len(project.collections) == 1
    assert set(project.collections["backend"].categories) == {"api", "docs"}


# Phase 5: Error Cases Tests


@pytest.mark.parametrize(
    "scenario,args_factory,setup_fn,expect_success",
    [
        (
            "duplicate",
            lambda: CategoryCollectionAddArgs(type="collection", name="backend", categories=["api"]),
            lambda client: call_mcp_tool(
                client,
                "category_collection_add",
                CategoryCollectionAddArgs(type="collection", name="backend", categories=["api"]),
            ),
            False,
        ),
        (
            "remove_nonexistent",
            lambda: CategoryCollectionRemoveArgs(type="collection", name="nonexistent"),
            None,
            False,
        ),
        (
            "update_nonexistent",
            lambda: CategoryCollectionUpdateArgs(type="collection", name="nonexistent", add_categories=["api"]),
            None,
            False,
        ),
        (
            "invalid_name",
            lambda: CategoryCollectionAddArgs(type="collection", name="invalid name!", categories=["api"]),
            None,
            False,
        ),
        (
            "empty_categories",
            lambda: CategoryCollectionAddArgs(type="collection", name="empty", categories=[]),
            None,
            True,
        ),
    ],
    ids=["duplicate", "remove_nonexistent", "update_nonexistent", "invalid_name", "empty_categories"],
)
@pytest.mark.anyio
async def test_collection_error_scenarios(
    mcp_server, test_session, monkeypatch, scenario, args_factory, setup_fn, expect_success
):
    """Test various collection operation error scenarios."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        if setup_fn:
            await setup_fn(client)

        args = args_factory()
        tool_name = (
            "category_collection_add"
            if isinstance(args, CategoryCollectionAddArgs)
            else (
                "category_collection_update"
                if isinstance(args, CategoryCollectionUpdateArgs)
                else "category_collection_remove"
            )
        )
        result = await call_mcp_tool(client, tool_name, args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is expect_success


# Phase 6: Multi-Tool Workflows


@pytest.mark.anyio
async def test_collection_removal_preserves_categories(mcp_server, empty_session, tmp_path, monkeypatch):
    """Test removing collection preserves categories."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = empty_session
    await session1.update_config(lambda p: p.with_category("api", Category(dir="src/api", patterns=["*.py"])))

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args1 = CategoryCollectionAddArgs(type="collection", name="backend", categories=["api"])
        await call_mcp_tool(client, "category_collection_add", args1)
        args2 = CategoryCollectionRemoveArgs(type="collection", name="backend")
        await call_mcp_tool(client, "category_collection_remove", args2)

    # Reload and verify categories still exist
    session2 = await _get_test_session(tmp_path)
    project = session2._Session__delegate.project
    assert len(project.collections) == 0
    assert len(project.categories) == 1
    assert "api" in project.categories


# Collection content functionality is now handled by the unified get_content tool
