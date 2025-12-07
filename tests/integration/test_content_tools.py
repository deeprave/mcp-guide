"""Integration tests for get_content unified access tool via MCP client."""

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
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_content", "tool_category", "tool_collection"])


@pytest.mark.anyio
async def test_get_content_category_only(mcp_server, tmp_path, monkeypatch):
    """Test get_content with category-only match."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category
    await session.update_config(lambda p: p.with_category(Category(name="guide", dir="guide", patterns=["*.md"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_content", {"category_or_collection": "guide"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Project Guidelines" in response["value"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_content_collection_only(mcp_server, tmp_path, monkeypatch):
    """Test get_content with collection-only match."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add categories and collection
    await session.update_config(
        lambda p: p.with_category(Category(name="guide", dir="guide", patterns=["*.md"]))
        .with_category(Category(name="lang", dir="lang", patterns=["*.md"]))
        .with_collection(Collection(name="all", categories=["guide", "lang"]))
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_content", {"category_or_collection": "all"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Project Guidelines" in response["value"]
        assert "Python Guide" in response["value"]

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_content_both_match_deduplicates(mcp_server, tmp_path, monkeypatch):
    """Test get_content when name matches both collection and category - should deduplicate."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category "guide" and collection "guide" containing "guide" category
    await session.update_config(
        lambda p: p.with_category(Category(name="guide", dir="guide", patterns=["*.md"])).with_collection(
            Collection(name="guide", categories=["guide"])
        )
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_content", {"category_or_collection": "guide"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        # File should appear only once (de-duplicated)
        content = response["value"]
        assert "Project Guidelines" in content
        # Count occurrences - should be 1 (in MIME header) + 1 (in content) = 2 total
        # If not de-duplicated, would appear 4 times
        assert content.count("guidelines.md") <= 3  # Allow for MIME headers

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_content_pattern_override(mcp_server, tmp_path, monkeypatch):
    """Test get_content with pattern override."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with multiple file types
    await session.update_config(
        lambda p: p.with_category(Category(name="context", dir="context", patterns=["*.md", "*.yaml"]))
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Call with pattern override to only get .md files
        result = await client.call_tool("get_content", {"category_or_collection": "context", "pattern": "*.md"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Jira Integration" in response["value"]
        assert "jira-settings.yaml" not in response["value"]  # YAML file should be excluded

    remove_current_session("test")


@pytest.mark.anyio
async def test_get_content_empty_result(mcp_server, tmp_path, monkeypatch):
    """Test get_content with no matching files."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))

    # Add category with no files
    await session.update_config(lambda p: p.with_category(Category(name="empty", dir="empty", patterns=["*.md"])))

    # Create empty directory
    docroot = Path(tmp_path.resolve()) / "docs"
    empty_dir = docroot / "empty"
    empty_dir.mkdir(parents=True, exist_ok=True)

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await client.call_tool("get_content", {"category_or_collection": "empty"})
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "No matching content found" in response["value"]
        assert "instruction" in response

    remove_current_session("test")
