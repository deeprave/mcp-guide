"""Integration tests for project management tools via MCP client.

Tests project tools through the MCP protocol interface to verify:
- Tool registration with MCP server
- End-to-end workflows through real client
- Configuration persistence across operations
- Multi-project scenarios
"""

from unittest.mock import patch

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_guide.tools.tool_category import CategoryAddArgs
from mcp_guide.tools.tool_project import (
    CloneProjectArgs,
    GetCurrentProjectArgs,
    ListProjectArgs,
    ListProjectsArgs,
    SetCurrentProjectArgs,
)
from tests.conftest import call_mcp_tool

# Module-level patches
_config_file_patch = None
_docroot_patch = None
_test_config_dir = None


@pytest.fixture(scope="module")
def setup_config_isolation(tmp_path_factory):
    """Setup module-wide config directory isolation."""
    global _config_file_patch, _docroot_patch, _test_config_dir
    _test_config_dir = tmp_path_factory.mktemp("test_config")

    # Start patches that will last for entire module
    _config_file_patch = patch(
        "mcp_guide.config_paths.get_config_file", lambda config_dir=None: _test_config_dir / "config.yaml"
    )
    _docroot_patch = patch("mcp_guide.config_paths.get_docroot", lambda config_dir=None: _test_config_dir / "docroot")

    _config_file_patch.start()
    _docroot_patch.start()

    yield

    # Stop patches after all tests in module complete
    _config_file_patch.stop()
    _docroot_patch.stop()


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory, setup_config_isolation):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_project", "tool_category", "tool_collection"])


# Registration Tests


@pytest.mark.anyio
async def test_get_current_project_registered(mcp_server):
    """Test that get_current_project is registered in MCP."""
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "get_current_project" in tool_names


@pytest.mark.anyio
async def test_set_current_project_registered(mcp_server):
    """Test that set_current_project is registered in MCP."""
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "set_current_project" in tool_names


@pytest.mark.anyio
async def test_list_projects_registered(mcp_server):
    """Test that list_projects is registered in MCP."""
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "list_projects" in tool_names


@pytest.mark.anyio
async def test_list_project_registered(mcp_server):
    """Test that list_project is registered in MCP."""
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "list_project" in tool_names


@pytest.mark.anyio
async def test_clone_project_registered(mcp_server):
    """Test that clone_project is registered in MCP."""
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "clone_project" in tool_names


# Read-Only Operations


@pytest.mark.anyio
async def test_get_current_project_non_verbose(mcp_server, monkeypatch):
    """Test getting current project in non-verbose mode."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = GetCurrentProjectArgs()
        result = await call_mcp_tool(client, "get_current_project", args)

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "collections" in content or "categories" in content


@pytest.mark.anyio
async def test_get_current_project_verbose(mcp_server, monkeypatch):
    """Test getting current project in verbose mode."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = GetCurrentProjectArgs(verbose=True)
        result = await call_mcp_tool(client, "get_current_project", args)

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "categories" in content or "collections" in content


@pytest.mark.anyio
async def test_list_projects_non_verbose(mcp_server):
    """Test listing all projects in non-verbose mode."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create test projects
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_beta"))
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_gamma"))

        args = ListProjectsArgs()
        result = await call_mcp_tool(client, "list_projects", args)

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "project_alpha" in content
        assert "project_beta" in content
        assert "project_gamma" in content


@pytest.mark.anyio
async def test_list_projects_verbose(mcp_server):
    """Test listing all projects in verbose mode."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create test projects
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_beta"))

        args = ListProjectsArgs(verbose=True)
        result = await call_mcp_tool(client, "list_projects", args)

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "project_alpha" in content
        assert "categories" in content or "collections" in content


@pytest.mark.anyio
async def test_list_project_by_name(mcp_server, monkeypatch):
    """Test getting specific project details by name."""
    monkeypatch.setenv("PWD", "/fake/path/project_alpha")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha with categories
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"]))

        args = ListProjectArgs(name="project_alpha")
        result = await call_mcp_tool(client, "list_project", args)

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "docs" in content
        assert "api" in content


@pytest.mark.anyio
async def test_list_project_invalid_name(mcp_server, monkeypatch):
    """Test getting non-existent project returns error."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = ListProjectArgs(name="nonexistent")
        result = await call_mcp_tool(client, "list_project", args)

        assert result.isError is False  # MCP call succeeds
        content = result.content[0].text  # type: ignore[union-attr]
        assert '"success": false' in content  # But tool returns error
        assert "not found" in content.lower()


# Project Switching


@pytest.mark.anyio
async def test_switch_to_existing_project(mcp_server, monkeypatch):
    """Test switching to an existing project."""
    monkeypatch.setenv("PWD", "/fake/path/project_alpha")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))

        # Switch to test project
        monkeypatch.setenv("PWD", "/fake/path/test")
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="test"))

        # Now switch back to project_alpha
        monkeypatch.setenv("PWD", "/fake/path/project_alpha")
        result = await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "project_alpha" in content

        # Verify current project changed
        verify_result = await call_mcp_tool(client, "get_current_project", GetCurrentProjectArgs())
        verify_content = verify_result.content[0].text  # type: ignore[union-attr]
        assert "docs" in verify_content or "api" in verify_content


@pytest.mark.anyio
async def test_switch_creates_new_project(mcp_server):
    """Test switching to non-existent project creates it."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        result = await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="new_project"))

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "new_project" in content

        # Verify project exists in list
        list_result = await call_mcp_tool(client, "list_projects", ListProjectsArgs())
        list_content = list_result.content[0].text  # type: ignore[union-attr]
        assert "new_project" in list_content


@pytest.mark.anyio
async def test_switch_verbose_mode(mcp_server):
    """Test switching with verbose mode returns full details."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_beta with some content
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_beta"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="test"))

        result = await call_mcp_tool(
            client, "set_current_project", SetCurrentProjectArgs(name="project_beta", verbose=True)
        )

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "project_beta" in content
        assert "categories" in content or "collections" in content


# Clone Operations


@pytest.mark.anyio
async def test_clone_to_current_merge(mcp_server, monkeypatch):
    """Test cloning to current project with merge mode."""
    monkeypatch.setenv("PWD", "/fake/path/project_alpha")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha with content
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"]))

        # Create empty project_gamma and switch to it
        monkeypatch.setenv("PWD", "/fake/path/project_gamma")
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_gamma"))

        # Clone alpha to current (gamma)
        result = await call_mcp_tool(client, "clone_project", CloneProjectArgs(from_project="project_alpha"))

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "categories_added" in content
        assert "2" in content  # 2 categories added


@pytest.mark.anyio
async def test_clone_to_different_merge(mcp_server):
    """Test cloning to different project with merge mode."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha with content
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"]))

        # Create empty project_gamma
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_gamma"))
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="test"))

        result = await call_mcp_tool(
            client, "clone_project", CloneProjectArgs(from_project="project_alpha", to_project="project_gamma")
        )

        assert result.isError is False

        # Verify gamma has alpha's config
        verify_result = await call_mcp_tool(client, "list_project", ListProjectArgs(name="project_gamma"))
        verify_content = verify_result.content[0].text  # type: ignore[union-attr]
        assert "docs" in verify_content or "api" in verify_content


@pytest.mark.anyio
async def test_clone_with_conflicts(mcp_server):
    """Test cloning with overlapping category names shows warnings."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha with docs category
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))

        # Create project_beta with different docs category
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_beta"))
        await call_mcp_tool(
            client, "category_add", CategoryAddArgs(name="docs", dir="documentation", patterns=["*.md", "*.rst"])
        )
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="test"))

        # Clone alpha to beta (both have "docs" category with different configs)
        result = await call_mcp_tool(
            client, "clone_project", CloneProjectArgs(from_project="project_alpha", to_project="project_beta")
        )

        assert result.isError is False
        content = result.content[0].text  # type: ignore[union-attr]
        assert "conflict" in content.lower() or "warning" in content.lower()


@pytest.mark.anyio
async def test_clone_replace_safeguard(mcp_server, monkeypatch):
    """Test clone replace mode without force triggers safeguard."""
    monkeypatch.setenv("PWD", "/fake/path/project_alpha")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))

        # Create project_beta with content
        monkeypatch.setenv("PWD", "/fake/path/project_beta")
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_beta"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="tests", dir="tests", patterns=["test_*.py"]))

        # Try to clone with replace mode (should fail without force)
        result = await call_mcp_tool(
            client,
            "clone_project",
            CloneProjectArgs(from_project="project_alpha", to_project="project_beta", merge=False),
        )

        assert result.isError is False  # MCP call succeeds
        content = result.content[0].text  # type: ignore[union-attr]
        assert '"success": false' in content  # But tool returns error
        assert "force" in content.lower()


@pytest.mark.anyio
async def test_clone_replace_force(mcp_server):
    """Test clone replace mode with force overrides safeguard."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))

        # Create project_beta with different content
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_beta"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="tests", dir="tests", patterns=["test_*.py"]))
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="test"))

        result = await call_mcp_tool(
            client,
            "clone_project",
            CloneProjectArgs(from_project="project_alpha", to_project="project_beta", merge=False, force=True),
        )

        assert result.isError is False

        # Verify beta now has only alpha's config
        verify_result = await call_mcp_tool(client, "list_project", ListProjectArgs(name="project_beta"))
        verify_content = verify_result.content[0].text  # type: ignore[union-attr]
        assert "docs" in verify_content
        assert "tests" not in verify_content  # Beta's original category should be gone


@pytest.mark.anyio
async def test_clone_updates_cache(mcp_server):
    """Test cloning to current project updates cache."""

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha with content
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"]))

        # Switch to gamma
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_gamma"))

        # Clone alpha to current
        await call_mcp_tool(client, "clone_project", CloneProjectArgs(from_project="project_alpha"))

        # Verify get_current shows new config
        result = await call_mcp_tool(client, "get_current_project", GetCurrentProjectArgs(verbose=True))
        content = result.content[0].text  # type: ignore[union-attr]
        assert "docs" in content or "api" in content


# Multi-Operation Workflow


@pytest.mark.anyio
async def test_complete_multi_project_workflow(mcp_server, monkeypatch):
    """Test complete workflow: list → switch → clone → verify."""
    monkeypatch.setenv("PWD", "/fake/path/project_alpha")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Create project_alpha with content
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_alpha"))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))
        await call_mcp_tool(client, "category_add", CategoryAddArgs(name="api", dir="src/api", patterns=["*.py"]))

        # Create empty project_gamma
        monkeypatch.setenv("PWD", "/fake/path/project_gamma")
        await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_gamma"))

        # List all projects
        list_result = await call_mcp_tool(client, "list_projects", ListProjectsArgs())
        assert "project_alpha" in list_result.content[0].text  # type: ignore[union-attr]

        # Switch to gamma (already there)
        switch_result = await call_mcp_tool(client, "set_current_project", SetCurrentProjectArgs(name="project_gamma"))
        assert switch_result.isError is False

        # Clone alpha to current
        clone_result = await call_mcp_tool(client, "clone_project", CloneProjectArgs(from_project="project_alpha"))
        assert clone_result.isError is False

        # Verify current project has cloned config
        verify_result = await call_mcp_tool(client, "get_current_project", GetCurrentProjectArgs(verbose=True))
        verify_content = verify_result.content[0].text  # type: ignore[union-attr]
        assert "docs" in verify_content or "api" in verify_content
