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
from mcp_guide.tools.tool_category import (
    CategoryAddArgs,
    CategoryContentArgs,
    CategoryListArgs,
    CategoryListFilesArgs,
    CategoryRemoveArgs,
    CategoryUpdateArgs,
)
from mcp_guide.tools.tool_collection import CollectionAddArgs
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
    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    yield session
    await remove_current_session("test")


# Basic CRUD Operations


@pytest.mark.anyio
async def test_add_category_via_mcp(mcp_server, test_session, monkeypatch):
    """Test adding category through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        result = await call_mcp_tool(client, "category_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "api" in response["value"]


@pytest.mark.anyio
async def test_list_categories_via_mcp(mcp_server, test_session, monkeypatch):
    """Test listing categories through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)
        args2 = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        await call_mcp_tool(client, "category_add", args2)

        args = CategoryListArgs(verbose=False)
        result = await call_mcp_tool(client, "category_list", args)
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
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)

        args = CategoryUpdateArgs(name="api", add_patterns=["*.pyi"])
        result = await call_mcp_tool(client, "category_update", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "api" in response["value"]


@pytest.mark.anyio
async def test_remove_category_via_mcp(mcp_server, test_session, monkeypatch):
    """Test removing category through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)

        args = CategoryRemoveArgs(name="api")
        result = await call_mcp_tool(client, "category_remove", args)
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
        args = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        result = await call_mcp_tool(client, "category_add", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # Update category
        args = CategoryUpdateArgs(name="api", add_patterns=["*.pyi"])
        result = await call_mcp_tool(client, "category_update", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # List categories
        args = CategoryListArgs(verbose=True)
        result = await call_mcp_tool(client, "category_list", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert response["success"] is True
        assert len(response["value"]) == 1
        assert response["value"][0]["name"] == "api"
        assert "*.pyi" in response["value"][0]["patterns"]

        # Remove category
        args = CategoryRemoveArgs(name="api")
        result = await call_mcp_tool(client, "category_remove", args)
        assert json.loads(result.content[0].text)["success"] is True  # type: ignore[union-attr]

        # Verify removal
        args = CategoryListArgs(verbose=True)
        result = await call_mcp_tool(client, "category_list", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]
        assert len(response["value"]) == 0


# Validation Tests


@pytest.mark.anyio
async def test_add_category_invalid_name_fails(mcp_server, test_session, monkeypatch):
    """Test adding category with invalid name fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryAddArgs(name="", dir="src/api", patterns=["*.py"])
        result = await call_mcp_tool(client, "category_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_add_category_invalid_patterns_fails(mcp_server, test_session, monkeypatch):
    """Test adding category with invalid patterns fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Use pattern with path traversal
        args = CategoryAddArgs(name="api", dir="src/api", patterns=["../*.py"])
        result = await call_mcp_tool(client, "category_add", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_add_category_duplicate_fails(mcp_server, test_session, monkeypatch):
    """Test adding duplicate category fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)

        args2 = CategoryAddArgs(name="api", dir="src/api2", patterns=["*.py"])
        result = await call_mcp_tool(client, "category_add", args2)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_update_nonexistent_category_fails(mcp_server, test_session, monkeypatch):
    """Test updating non-existent category fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryUpdateArgs(name="nonexistent", add_patterns=["*.py"])
        result = await call_mcp_tool(client, "category_update", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert "error" in response


@pytest.mark.anyio
async def test_remove_nonexistent_category_fails(mcp_server, test_session, monkeypatch):
    """Test removing non-existent category fails."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryRemoveArgs(name="nonexistent")
        result = await call_mcp_tool(client, "category_remove", args)
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
        args = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args)

    await remove_current_session("test")

    # Reload session and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert "api" in project.categories
    assert project.categories["api"].dir == "src/api/"
    assert "*.py" in project.categories["api"].patterns

    await remove_current_session("test")


@pytest.mark.anyio
async def test_category_persists_after_update(mcp_server, tmp_path, monkeypatch):
    """Test category persists after update."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add/update category
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)
        args2 = CategoryUpdateArgs(name="api", add_patterns=["*.pyi"])
        await call_mcp_tool(client, "category_update", args2)

    await remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert "*.pyi" in project.categories["api"].patterns

    await remove_current_session("test")


@pytest.mark.anyio
async def test_category_removed_persists(mcp_server, tmp_path, monkeypatch):
    """Test category removal persists."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session and add/remove category
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)
        args2 = CategoryRemoveArgs(name="api")
        await call_mcp_tool(client, "category_remove", args2)

    await remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 0

    await remove_current_session("test")


@pytest.mark.anyio
async def test_multiple_operations_persist(mcp_server, tmp_path, monkeypatch):
    """Test multiple operations persist correctly."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    # Create session with multiple operations
    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)
        args2 = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        await call_mcp_tool(client, "category_add", args2)
        args3 = CategoryUpdateArgs(name="api", add_patterns=["*.pyi"])
        await call_mcp_tool(client, "category_update", args3)
        args4 = CategoryRemoveArgs(name="docs")
        await call_mcp_tool(client, "category_remove", args4)

    await remove_current_session("test")

    # Reload and verify
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert "*.pyi" in project.categories["api"].patterns

    await remove_current_session("test")


# Integration Tests


@pytest.mark.anyio
async def test_category_removal_preserves_collections(mcp_server, tmp_path, monkeypatch):
    """Test removing category updates collections by removing the category reference."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)
        args2 = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        await call_mcp_tool(client, "category_add", args2)
        args3 = CollectionAddArgs(name="backend", categories=["api", "docs"])
        await call_mcp_tool(client, "collection_add", args3)

        # Remove one category
        args4 = CategoryRemoveArgs(name="api")
        await call_mcp_tool(client, "category_remove", args4)

    await remove_current_session("test")

    # Reload and verify collection still exists but category reference is removed
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.collections) == 1
    assert "backend" in project.collections
    assert "api" not in project.collections["backend"].categories  # Category reference removed
    assert "docs" in project.collections["backend"].categories  # Other category remains

    await remove_current_session("test")


@pytest.mark.anyio
async def test_update_category_preserves_collections(mcp_server, tmp_path, monkeypatch):
    """Test updating category preserves collections."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session1 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args1 = CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"])
        await call_mcp_tool(client, "category_add", args1)
        args2 = CollectionAddArgs(name="backend", categories=["api"])
        await call_mcp_tool(client, "collection_add", args2)

        # Update category
        args3 = CategoryUpdateArgs(name="api", add_patterns=["*.pyi"])
        await call_mcp_tool(client, "category_update", args3)

    await remove_current_session("test")

    # Reload and verify both category and collection
    session2 = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    project = await session2.get_project()
    assert len(project.categories) == 1
    assert "*.pyi" in project.categories["api"].patterns
    assert len(project.collections) == 1
    assert "backend" in project.collections
    assert "api" in project.collections["backend"].categories

    await remove_current_session("test")


# Phase 7: Category Content Retrieval


@pytest.mark.anyio
async def test_category_content_not_found(mcp_server, tmp_path, monkeypatch):
    """Test error when category doesn't exist."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryContentArgs(category="nonexistent")
        result = await call_mcp_tool(client, "category_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "not_found"
        assert "nonexistent" in response["error"]

    await remove_current_session("test")


@pytest.mark.anyio
async def test_category_content_empty_category(mcp_server, tmp_path, monkeypatch):
    """Test success message when category has no matching files."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern that won't match any files
    await session.update_config(lambda p: p.with_category("guide", Category(dir="guide", patterns=["nomatch*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryContentArgs(category="guide")
        result = await call_mcp_tool(client, "category_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "no files found" in response["value"].lower() or "no matching content" in response["value"].lower()

    await remove_current_session("test")


@pytest.mark.anyio
async def test_category_content_success_single_file(mcp_server, tmp_path, monkeypatch):
    """Test successful content retrieval with single file."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern matching single file
    await session.update_config(lambda p: p.with_category("lang", Category(dir="lang", patterns=["python*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryContentArgs(category="lang")
        result = await call_mcp_tool(client, "category_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Python Guide" in response["value"]
        assert "Java Guide" not in response["value"]

    await remove_current_session("test")


@pytest.mark.anyio
async def test_category_content_success_multiple_files(mcp_server, tmp_path, monkeypatch):
    """Test successful content retrieval with multiple files."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern matching multiple files
    await session.update_config(lambda p: p.with_category("context", Category(dir="context", patterns=["jira*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryContentArgs(category="context")
        result = await call_mcp_tool(client, "category_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Jira Integration" in response["value"]
        assert "jira:" in response["value"]  # From jira-settings.yaml
        assert "Development Standards" not in response["value"]

    await remove_current_session("test")


@pytest.mark.anyio
async def test_category_content_pattern_override(mcp_server, tmp_path, monkeypatch):
    """Test pattern overrides category defaults."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with pattern matching all files
    await session.update_config(lambda p: p.with_category("guide", Category(dir="guide", patterns=["*"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Request only files matching "guidelines-*"
        args = CategoryContentArgs(category="guide", pattern="guidelines-*")
        result = await call_mcp_tool(client, "category_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Feature 1 Guidelines" in response["value"]
        assert "Project Guidelines" not in response["value"]

    await remove_current_session("test")


@pytest.mark.anyio
async def test_category_content_file_read_error(mcp_server, tmp_path, monkeypatch):
    """Test error handling when file cannot be read."""
    import os

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category
    await session.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))

    # Create test file and make it unreadable
    docroot = Path(tmp_path.resolve()) / "docs" / "docs"
    docroot.mkdir(parents=True, exist_ok=True)
    test_file = docroot / "test.md"
    test_file.write_text("# Test Content")
    os.chmod(test_file, 0o000)

    try:
        async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
            args = CategoryContentArgs(category="docs")
            result = await call_mcp_tool(client, "category_content", args)
            response = json.loads(result.content[0].text)  # type: ignore[union-attr]

            assert response["success"] is False
            assert response["error_type"] == "file_read_error"
            assert "test.md" in response["error"]
    finally:
        # Restore permissions for cleanup
        os.chmod(test_file, 0o644)

    await remove_current_session("test")


# File Listing Tests


async def test_category_list_files_success(mcp_server, tmp_path, monkeypatch):
    """Test successful file listing in category."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    # Add category with pattern matching files
    await session.update_config(lambda p: p.with_category("guide", Category(dir="guide", patterns=["general*"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryListFilesArgs(name="guide")
        result = await call_mcp_tool(client, "category_list_files", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        files = response["value"]
        assert isinstance(files, list)
        assert len(files) > 0

        # Check file structure
        file_info = files[0]
        assert "path" in file_info
        assert "size" in file_info
        assert "basename" in file_info

    await remove_current_session("test")


async def test_category_list_files_mixed_file_types(mcp_server, tmp_path, monkeypatch):
    """Test file listing with mixed file types and subdirectories."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    # Create additional mixed files
    guide_dir = docroot / "guide"
    guide_dir.mkdir(exist_ok=True)
    (guide_dir / "readme.md").write_text("# README")
    (guide_dir / "config.json.mustache").write_text('{"name": "{{name}}"}')
    (guide_dir / "subdir").mkdir()
    (guide_dir / "subdir" / "nested.txt").write_text("nested content")

    # Add category that matches all files
    await session.update_config(lambda p: p.with_category("guide", Category(dir="guide", patterns=["**/*"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryListFilesArgs(name="guide")
        result = await call_mcp_tool(client, "category_list_files", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        files = response["value"]
        assert len(files) >= 3

        # Check mixed file types are included
        basenames = [f["basename"] for f in files]
        assert "readme.md" in basenames
        assert "config.json" in basenames  # .mustache stripped
        assert "nested.txt" in basenames

        # Verify subdirectory paths
        paths = [f["path"] for f in files]
        assert any("subdir/nested.txt" in path for path in paths)

    await remove_current_session("test")


async def test_category_list_files_output_format(mcp_server, tmp_path, monkeypatch):
    """Test 2-column output format with path and size."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    docroot = Path(tmp_path.resolve()) / "docs"

    # Create test files with known content
    test_dir = docroot / "test"
    test_dir.mkdir(parents=True)
    (test_dir / "small.txt").write_text("small")  # 5 bytes
    (test_dir / "large.md").write_text("# Large Content\n" + "x" * 100)  # >100 bytes

    await session.update_config(lambda p: p.with_category("test", Category(dir="test", patterns=["*"])))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryListFilesArgs(name="test")
        result = await call_mcp_tool(client, "category_list_files", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        files = response["value"]
        assert len(files) == 2

        # Verify 2-column format structure
        for file_info in files:
            assert "path" in file_info
            assert "size" in file_info
            assert "basename" in file_info
            assert isinstance(file_info["path"], str)
            assert isinstance(file_info["size"], int)
            assert isinstance(file_info["basename"], str)
            assert file_info["size"] > 0

        # Check specific file sizes
        small_file = next(f for f in files if f["basename"] == "small.txt")
        large_file = next(f for f in files if f["basename"] == "large.md")
        assert small_file["size"] == 5
        assert large_file["size"] > 100

    await remove_current_session("test")


async def test_category_list_files_category_not_found_integration(mcp_server, tmp_path, monkeypatch):
    """Test category not found error through MCP."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = CategoryListFilesArgs(name="nonexistent")
        result = await call_mcp_tool(client, "category_list_files", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "not_found"
        assert "nonexistent" in response["error"]

    await remove_current_session("test")
