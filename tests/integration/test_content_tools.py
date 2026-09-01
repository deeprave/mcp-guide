"""Integration tests for get_content unified access tool via MCP client."""

import inspect
import json
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastmcp.client import Client, FastMCPTransport

from mcp_guide.models import Category, Collection
from mcp_guide.session import Session, get_session
from mcp_guide.tools.tool_content import ContentArgs
from tests.conftest import call_mcp_tool
from tests.helpers import create_unbound_test_session


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


async def _create_bound_session(tmp_path: Path) -> Session:
    """Create a lightweight bound session for integration tests."""
    config_dir = str(tmp_path.resolve())
    session = create_unbound_test_session(config_dir)
    project_root = Path(config_dir) / "client-roots" / "test"
    project_root.mkdir(parents=True, exist_ok=True)
    await session.bind_project_path(project_root)
    return session


def _route_legacy_session(mcp_server, monkeypatch, session: Session) -> None:
    """Route the in-process legacy client to its isolated test Session."""
    runtime = inspect.getclosurevars(mcp_server._lifespan).nonlocals["runtime"]
    original_session_request = runtime.session_request

    @asynccontextmanager
    async def session_request(owner):
        runtime.retain_session(owner, session)
        async with original_session_request(owner) as resolved_session:
            yield resolved_session

    monkeypatch.setattr(runtime, "session_request", session_request)


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_content", "tool_category", "tool_collection"])


@pytest.mark.anyio
async def test_get_content_category_only(mcp_server, tmp_path, monkeypatch):
    """Test get_content with category-only match."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await _create_bound_session(tmp_path)
    _route_legacy_session(mcp_server, monkeypatch, session)

    # Add category
    await session.update_config(lambda p: p.with_category("guide", Category(dir="guide", patterns=["*.md"])))

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = ContentArgs(expression="guide")
        result = await call_mcp_tool(client, "get_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Project Guidelines" in response["value"]


@pytest.mark.anyio
async def test_get_content_collection_only(mcp_server, tmp_path, monkeypatch):
    """Test get_content with collection-only match."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    _route_legacy_session(mcp_server, monkeypatch, session)

    # Add categories and collection
    await session.update_config(
        lambda p: (
            p.with_category("guide", Category(dir="guide", patterns=["*.md"]))
            .with_category("lang", Category(dir="lang", patterns=["*.md"]))
            .with_collection("all", Collection(categories=["guide", "lang"]))
        )
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    guide_dir = docroot / "guide"
    lang_dir = docroot / "lang"
    guide_dir.mkdir(parents=True, exist_ok=True)
    lang_dir.mkdir(parents=True, exist_ok=True)
    (guide_dir / "guidelines.md").write_text("# Project Guidelines\n")
    (lang_dir / "python.md").write_text("# Python Guide\n")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = ContentArgs(expression="all")
        result = await call_mcp_tool(client, "get_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Project Guidelines" in response["value"]
        assert "Python Guide" in response["value"]


@pytest.mark.anyio
async def test_get_content_both_match_deduplicates(mcp_server, tmp_path, monkeypatch):
    """Test get_content when name matches both collection and category - should deduplicate."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    _route_legacy_session(mcp_server, monkeypatch, session)

    # Add category "guide" and collection "guide" containing "guide" category
    await session.update_config(
        lambda p: p.with_category("guide", Category(dir="guide", patterns=["*.md"])).with_collection(
            "guide", Collection(categories=["guide"])
        )
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = ContentArgs(expression="guide")
        result = await call_mcp_tool(client, "get_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        # File should appear only once (de-duplicated)
        content = response["value"]
        assert "Project Guidelines" in content
        # Count occurrences - should be 1 (in MIME header) + 1 (in content) = 2 total
        # If not de-duplicated, would appear 4 times
        assert content.count("guidelines.md") <= 3  # Allow for MIME headers


@pytest.mark.anyio
async def test_get_content_pattern_override(mcp_server, tmp_path, monkeypatch):
    """Test get_content with pattern override."""
    from .test_data_generator import generate_test_files

    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    _route_legacy_session(mcp_server, monkeypatch, session)

    # Add category with multiple file types
    await session.update_config(
        lambda p: p.with_category("context", Category(dir="context", patterns=["*.md", "*.yaml"]))
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    generate_test_files(docroot)

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        # Call with pattern override to only get .md files
        args = ContentArgs(expression="context", pattern="*.md")
        result = await call_mcp_tool(client, "get_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Jira Integration" in response["value"]
        assert "jira-settings.yaml" not in response["value"]  # YAML file should be excluded


@pytest.mark.anyio
async def test_get_content_empty_result(mcp_server, tmp_path, monkeypatch):
    """Test get_content with no matching files."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path.resolve()))
    _route_legacy_session(mcp_server, monkeypatch, session)

    # Add category with no files
    session._Session__delegate.bind(
        session._Session__delegate.project.with_category("empty", Category(dir="empty", patterns=["*.md"]))
    )

    # Create empty directory
    docroot = Path(tmp_path.resolve()) / "docs"
    empty_dir = docroot / "empty"
    empty_dir.mkdir(parents=True, exist_ok=True)

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = ContentArgs(expression="empty")
        result = await call_mcp_tool(client, "get_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "No matching content found" in response["value"]
        assert "instruction" in response


@pytest.mark.anyio
async def test_get_content_nested_collection(mcp_server, tmp_path, monkeypatch):
    """Test get_content with nested collection reference."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await _create_bound_session(tmp_path)
    _route_legacy_session(mcp_server, monkeypatch, session)
    session._Session__delegate.bind(
        session._Session__delegate.project.with_category("guide", Category(dir="guide", patterns=["*.md"]))
        .with_category("lang", Category(dir="lang", patterns=["*.md"]))
        .with_collection("docs", Collection(categories=["guide"]))
        .with_collection("all", Collection(categories=["docs", "lang"]))
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    guide_dir = docroot / "guide"
    lang_dir = docroot / "lang"
    guide_dir.mkdir(parents=True, exist_ok=True)
    lang_dir.mkdir(parents=True, exist_ok=True)
    (guide_dir / "guidelines.md").write_text("# Project Guidelines\n")
    (lang_dir / "python.md").write_text("# Python Guide\n")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = ContentArgs(expression="all")
        result = await call_mcp_tool(client, "get_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "Project Guidelines" in response["value"]  # From guide (via docs collection)
        assert "Python Guide" in response["value"]  # From lang


@pytest.mark.anyio
async def test_get_content_circular_collection_reference(mcp_server, tmp_path, monkeypatch):
    """Test get_content with circular collection references."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    session = await _create_bound_session(tmp_path)
    _route_legacy_session(mcp_server, monkeypatch, session)
    session._Session__delegate.bind(
        session._Session__delegate.project.with_category("guide", Category(dir="guide", patterns=["*.md"]))
        .with_category("lang", Category(dir="lang", patterns=["*.md"]))
        .with_collection("col1", Collection(categories=["guide", "col2"]))
        .with_collection("col2", Collection(categories=["lang", "col1"]))
    )

    docroot = Path(tmp_path.resolve()) / "docs"
    guide_dir = docroot / "guide"
    lang_dir = docroot / "lang"
    guide_dir.mkdir(parents=True, exist_ok=True)
    lang_dir.mkdir(parents=True, exist_ok=True)
    (guide_dir / "guidelines.md").write_text("# Project Guidelines\n")
    (lang_dir / "python.md").write_text("# Python Guide\n")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        args = ContentArgs(expression="col1")
        result = await call_mcp_tool(client, "get_content", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        # Should not hang or error - circular reference should be handled
        assert response["success"] is True
        assert "Project Guidelines" in response["value"]  # From guide
        assert "Python Guide" in response["value"]  # From lang
