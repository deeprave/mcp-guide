"""Integration tests for feature flag tools.

Tests feature flag tools through MCP protocol with real session management.
"""

import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Project
from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_feature_flags import GetFlagArgs, ListFlagsArgs, SetFlagArgs
from tests.conftest import call_mcp_tool


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_feature_flags"])


@pytest.fixture
def test_session(tmp_path):
    """Create test session with sample project."""
    manager = ConfigManager(config_dir=str(tmp_path))
    session = Session(_config_manager=manager, project_name="test")

    # Create sample project with categories
    category = Category(
        name="docs",
        dir="documentation",
        patterns=["*.md", "*.txt"],
    )
    session._cached_project = Project(name="test", categories=[category], collections=[])

    set_current_session(session)
    yield session
    remove_current_session("test")


@pytest.mark.anyio
async def test_set_flag_via_mcp(mcp_server, test_session, monkeypatch):
    """Test setting feature flag through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Set a project flag
        args = SetFlagArgs(feature_name="test_flag", value=True)
        result = await call_mcp_tool(client, "set_flag", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "test_flag" in response["value"]


@pytest.mark.anyio
async def test_list_flags_via_mcp(mcp_server, test_session, monkeypatch):
    """Test listing feature flags through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # First set a flag
        set_args = SetFlagArgs(feature_name="list_test", value="test_value")
        await call_mcp_tool(client, "set_flag", set_args)

        # Then list flags
        list_args = ListFlagsArgs()
        result = await call_mcp_tool(client, "list_flags", list_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "list_test" in response["value"]
        assert response["value"]["list_test"] == "test_value"


@pytest.mark.anyio
async def test_get_flag_via_mcp(mcp_server, test_session, monkeypatch):
    """Test getting feature flag through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # First set a flag
        set_args = SetFlagArgs(feature_name="get_test", value=["list", "value"])
        await call_mcp_tool(client, "set_flag", set_args)

        # Then get the flag
        get_args = GetFlagArgs(feature_name="get_test")
        result = await call_mcp_tool(client, "get_flag", get_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert response["value"] == ["list", "value"]


@pytest.mark.anyio
async def test_flag_validation_via_mcp(mcp_server, test_session, monkeypatch):
    """Test flag validation through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # Try to set flag with invalid name (contains period)
        args = SetFlagArgs(feature_name="invalid.flag", value=True)
        result = await call_mcp_tool(client, "set_flag", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "validation_error"
        assert "periods" in response["error"].lower()


@pytest.mark.anyio
async def test_remove_flag_via_mcp(mcp_server, test_session, monkeypatch):
    """Test removing feature flag through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        # First set a flag
        set_args = SetFlagArgs(feature_name="remove_test", value=True)
        await call_mcp_tool(client, "set_flag", set_args)

        # Remove the flag
        remove_args = SetFlagArgs(feature_name="remove_test", value=None)
        result = await call_mcp_tool(client, "set_flag", remove_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "removed" in response["value"].lower()

        # Verify flag is gone
        get_args = GetFlagArgs(feature_name="remove_test")
        result = await call_mcp_tool(client, "get_flag", get_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        # When flag doesn't exist, value should be None
        assert response.get("value") is None
