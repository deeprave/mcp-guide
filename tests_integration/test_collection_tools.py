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

from mcp_guide.models import Category, Collection
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
    # Resolve symlinks to avoid path mismatch issues on macOS
    resolved_tmp_path = tmp_path.resolve()
    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(resolved_tmp_path))

    # Setup initial categories
    await session.update_config(
        lambda p: p.with_category(Category(name="api", dir="src/api", patterns=["*.py"]))
        .with_category(Category(name="tests", dir="tests", patterns=["test_*.py"]))
        .with_category(Category(name="docs", dir="docs", patterns=["*.md"]))
    )

    yield session
    remove_current_session("test")


# Phase 2: Collection Management Workflow Tests


@pytest.mark.anyio
async def test_add_collection_via_mcp(mcp_server, test_session, monkeypatch):
    """Test adding collection through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool(
            "collection_add", {"name": "backend", "categories": ["api", "tests"], "description": "Backend code"}
        )
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True


@pytest.mark.anyio
async def test_list_collections_via_mcp(mcp_server, test_session, monkeypatch):
    """Test listing collections through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add collection
        await client.call_tool(
            "collection_add", {"name": "backend", "categories": ["api", "tests"], "description": "Backend code"}
        )

        # List collections
        result = await client.call_tool("collection_list", {"verbose": True})
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
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api", "tests"]})

        # Update collection
        result = await client.call_tool("collection_update", {"name": "backend", "add_categories": ["docs"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True

        # Verify update
        result = await client.call_tool("collection_list", {"verbose": True})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        collections = response["value"]
        assert "docs" in collections[0]["categories"]


@pytest.mark.anyio
async def test_remove_collection_via_mcp(mcp_server, test_session, monkeypatch):
    """Test removing collection through MCP client."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add collection
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})

        # Remove collection
        result = await client.call_tool("collection_remove", {"name": "backend"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True

        # Verify removed
        result = await client.call_tool("collection_list", {"verbose": True})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        collections = response["value"]
        assert len(collections) == 0


@pytest.mark.anyio
async def test_collection_management_workflow(mcp_server, test_session, monkeypatch):
    """Test complete collection management workflow through MCP client."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add
        result = await client.call_tool(
            "collection_add", {"name": "backend", "categories": ["api", "tests"], "description": "Backend code"}
        )
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify added
        result = await client.call_tool("collection_list", {"verbose": True})
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert len(collections) == 1
        assert collections[0]["name"] == "backend"

        # Update - add category
        result = await client.call_tool("collection_update", {"name": "backend", "add_categories": ["docs"]})
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify updated
        result = await client.call_tool("collection_list", {"verbose": True})
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert "docs" in collections[0]["categories"]

        # Remove
        result = await client.call_tool("collection_remove", {"name": "backend"})
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List - verify removed
        result = await client.call_tool("collection_list", {"verbose": True})
        collections = json.loads(result.content[0].text)["value"]  # type: ignore[union-attr]
        assert len(collections) == 0


# Phase 3: Category Validation Integration Tests


@pytest.mark.anyio
async def test_add_collection_invalid_category_fails(mcp_server, test_session, monkeypatch):
    """Test adding collection with invalid category fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("collection_add", {"name": "backend", "categories": ["nonexistent"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "nonexistent" in response["error"].lower() or "invalid" in response["error"].lower()


@pytest.mark.anyio
async def test_update_collection_invalid_category_fails(mcp_server, test_session, monkeypatch):
    """Test updating collection with invalid category fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Add valid collection
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})

        # Try to update with invalid category
        result = await client.call_tool("collection_update", {"name": "backend", "add_categories": ["nonexistent"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "nonexistent" in response["error"].lower() or "invalid" in response["error"].lower()


@pytest.mark.anyio
async def test_validation_errors_return_proper_format(mcp_server, test_session, monkeypatch):
    """Test validation errors return proper Result format."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("collection_add", {"name": "backend", "categories": ["nonexistent"]})
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
    await session1.update_config(lambda p: p.with_category(Category(name="api", dir="src/api", patterns=["*.py"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})

    remove_current_session("test")

    # Reload session and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    assert project.collections[0].name == "backend"
    remove_current_session("test")


@pytest.mark.anyio
async def test_collection_persists_after_update(mcp_server, tmp_path, monkeypatch):
    """Test collection persists after update."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(
        lambda p: p.with_category(Category(name="api", dir="src/api", patterns=["*.py"])).with_category(
            Category(name="docs", dir="docs", patterns=["*.md"])
        )
    )

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})
        await client.call_tool("collection_update", {"name": "backend", "add_categories": ["docs"]})

    remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    assert "docs" in project.collections[0].categories
    remove_current_session("test")


@pytest.mark.anyio
async def test_collection_removed_persists(mcp_server, tmp_path, monkeypatch):
    """Test collection removal persists."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add collection
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(lambda p: p.with_category(Category(name="api", dir="src/api", patterns=["*.py"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})
        await client.call_tool("collection_remove", {"name": "backend"})

    remove_current_session("test")

    # Reload and verify removed
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 0
    remove_current_session("test")


@pytest.mark.anyio
async def test_multiple_operations_persist(mcp_server, tmp_path, monkeypatch):
    """Test multiple operations persist correctly."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(
        lambda p: p.with_category(Category(name="api", dir="src/api", patterns=["*.py"])).with_category(
            Category(name="docs", dir="docs", patterns=["*.md"])
        )
    )

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})
        await client.call_tool("collection_add", {"name": "frontend", "categories": ["docs"]})
        await client.call_tool("collection_update", {"name": "backend", "add_categories": ["docs"]})
        await client.call_tool("collection_remove", {"name": "frontend"})

    remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    assert project.collections[0].name == "backend"
    assert set(project.collections[0].categories) == {"api", "docs"}
    remove_current_session("test")


# Phase 5: Error Cases Tests


@pytest.mark.anyio
async def test_add_duplicate_collection_fails(mcp_server, test_session, monkeypatch):
    """Test adding duplicate collection fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})

        # Try to add duplicate
        result = await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "backend" in response["error"].lower() or "exists" in response["error"].lower()


@pytest.mark.anyio
async def test_remove_nonexistent_collection_fails(mcp_server, test_session, monkeypatch):
    """Test removing non-existent collection fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("collection_remove", {"name": "nonexistent"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False


@pytest.mark.anyio
async def test_update_nonexistent_collection_fails(mcp_server, test_session, monkeypatch):
    """Test updating non-existent collection fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("collection_update", {"name": "nonexistent", "add_categories": ["api"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False


@pytest.mark.anyio
async def test_add_collection_invalid_name_fails(mcp_server, test_session, monkeypatch):
    """Test adding collection with invalid name fails."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("collection_add", {"name": "invalid name!", "categories": ["api"]})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False


@pytest.mark.anyio
async def test_add_collection_empty_categories(mcp_server, test_session, monkeypatch):
    """Test adding collection with empty categories succeeds."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("collection_add", {"name": "empty", "categories": []})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True


# Phase 6: Multi-Tool Workflows


@pytest.mark.anyio
async def test_collection_removal_preserves_categories(mcp_server, tmp_path, monkeypatch):
    """Test removing collection preserves categories."""

    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with categories
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    await session1.update_config(lambda p: p.with_category(Category(name="api", dir="src/api", patterns=["*.py"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        await client.call_tool("collection_add", {"name": "backend", "categories": ["api"]})
        await client.call_tool("collection_remove", {"name": "backend"})

    remove_current_session("test")

    # Reload and verify categories still exist
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 0
    assert len(project.categories) == 1
    assert project.categories[0].name == "api"
    remove_current_session("test")


# Phase 7: Collection Content Retrieval


@pytest.mark.anyio
async def test_collection_content_args_valid():
    """Test CollectionContentArgs accepts valid inputs."""
    from mcp_guide.tools.tool_collection import CollectionContentArgs

    args = CollectionContentArgs(collection="docs")
    assert args.collection == "docs"
    assert args.pattern is None


@pytest.mark.anyio
async def test_collection_content_args_with_pattern():
    """Test CollectionContentArgs with pattern."""
    from mcp_guide.tools.tool_collection import CollectionContentArgs

    args = CollectionContentArgs(collection="docs", pattern="*.md")
    assert args.pattern == "*.md"


@pytest.mark.anyio
async def test_get_collection_content_not_found(mcp_server, tmp_path, monkeypatch):
    """Test error when collection doesn't exist."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with no collections
    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_collection_content", {"collection": "nonexistent"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "not_found"
        assert "nonexistent" in response["error"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_collection_content_category_not_found(mcp_server, tmp_path, monkeypatch):
    """Test error when category in collection doesn't exist."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with collection referencing non-existent category
    from mcp_guide.models import Collection

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    await session.update_config(
        lambda p: p.with_collection(Collection(name="test-collection", categories=["nonexistent"]))
    )

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_collection_content", {"collection": "test-collection"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "not_found"
        assert "category" in response["error"].lower()

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_collection_content_empty_collection(mcp_server, tmp_path, monkeypatch):
    """Test success message when collection has no matching files."""
    from tests_integration.test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern that won't match
    await session.update_config(
        lambda p: p.with_category(Category(name="guide", dir="guide", patterns=["nomatch*"])).with_collection(
            Collection(name="empty-collection", categories=["guide"])
        )
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_collection_content", {"collection": "empty-collection"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "no matching content" in response["value"].lower()

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_collection_content_success_single_category(mcp_server, tmp_path, monkeypatch):
    """Test successful content retrieval from single category."""
    from tests_integration.test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category matching python files only
    await session.update_config(
        lambda p: p.with_category(Category(name="lang", dir="lang", patterns=["python*"])).with_collection(
            Collection(name="test-collection", categories=["lang"])
        )
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_collection_content", {"collection": "test-collection"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Python Guide" in response["value"]
        assert "Java Guide" not in response["value"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_collection_content_success_multiple_categories(mcp_server, tmp_path, monkeypatch):
    """Test successful content retrieval from multiple categories."""
    from tests_integration.test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add categories with different patterns
    await session.update_config(
        lambda p: p.with_category(Category(name="lang", dir="lang", patterns=["kotlin*"]))
        .with_category(Category(name="context", dir="context", patterns=["standards*"]))
        .with_collection(Collection(name="all-docs", categories=["lang", "context"]))
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_collection_content", {"collection": "all-docs"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Kotlin Guide" in response["value"]
        assert "Development Standards" in response["value"]
        assert "Python Guide" not in response["value"]
        # Verify category-prefixed basenames in separators
        assert "--- lang/kotlin.md ---" in response["value"]
        assert "--- context/standards.md ---" in response["value"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_collection_content_pattern_override(mcp_server, tmp_path, monkeypatch):
    """Test pattern overrides category defaults."""
    from tests_integration.test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category matching all guide files
    await session.update_config(
        lambda p: p.with_category(Category(name="guide", dir="guide", patterns=["*"])).with_collection(
            Collection(name="test-collection", categories=["guide"])
        )
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Request only files matching "guidelines-*"
        result = await client.call_tool(
            "get_collection_content", {"collection": "test-collection", "pattern": "guidelines-*"}
        )
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Feature 1 Guidelines" in response["value"]
        assert "Project Guidelines" not in response["value"]

    remove_current_session("test")
