"""Integration tests for feature flag tools.

Tests feature flag tools through MCP protocol with real session management.
"""

import json

import pytest
from fastmcp.client import Client, FastMCPTransport

from mcp_guide.session import remove_current_session, set_current_session
from mcp_guide.tools.tool_feature_flags import ListFlagsArgs, SetFlagArgs
from tests.conftest import call_mcp_tool
from tests.helpers import create_test_session


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_feature_flags"])


@pytest.fixture
async def test_session(tmp_path):
    """Create test session with sample project."""
    session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))

    # Initialize project properly to set _project_key
    await session.get_project()

    set_current_session(session)
    yield session
    # Properly cleanup async session
    await remove_current_session()


@pytest.mark.anyio
async def test_set_project_flag_via_mcp(mcp_server, test_session, monkeypatch):
    """Test setting feature flag through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        # Set a project flag
        args = SetFlagArgs(feature_name="test_flag", value=True)
        result = await call_mcp_tool(client, "set_project_flag", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "test_flag" in response["value"]


@pytest.mark.anyio
async def test_list_project_flags_via_mcp(mcp_server, test_session, monkeypatch):
    """Test listing feature flags through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        # First set a flag
        set_args = SetFlagArgs(feature_name="list_test", value="test_value")
        await call_mcp_tool(client, "set_project_flag", set_args)

        # Then list flags
        list_args = ListFlagsArgs()
        result = await call_mcp_tool(client, "list_project_flags", list_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "list_test" in response["value"]
        assert response["value"]["list_test"] == "test_value"


@pytest.mark.anyio
async def test_get_project_flag_via_mcp(mcp_server, test_session, monkeypatch):
    """Test getting feature flag through MCP client using list_project_flags with feature_name."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        # First set a flag
        set_args = SetFlagArgs(feature_name="get_test", value=["list", "value"])
        await call_mcp_tool(client, "set_project_flag", set_args)

        # Then get the flag using list_project_flags with feature_name
        get_args = ListFlagsArgs(feature_name="get_test")
        result = await call_mcp_tool(client, "list_project_flags", get_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert response["value"] == ["list", "value"]


@pytest.mark.anyio
async def test_flag_validation_via_mcp(mcp_server, test_session, monkeypatch):
    """Test flag validation through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        # Try to set flag with invalid name (contains period)
        args = SetFlagArgs(feature_name="invalid.flag", value=True)
        result = await call_mcp_tool(client, "set_project_flag", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "validation_error"
        assert "periods" in response["error"].lower()


@pytest.mark.anyio
async def test_remove_flag_via_mcp(mcp_server, test_session, monkeypatch):
    """Test removing feature flag through MCP client."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        # First set a flag
        set_args = SetFlagArgs(feature_name="remove_test", value=True)
        await call_mcp_tool(client, "set_project_flag", set_args)

        # Remove the flag
        remove_args = SetFlagArgs(feature_name="remove_test", value=None)
        result = await call_mcp_tool(client, "set_project_flag", remove_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert "removed" in response["value"].lower()

        # Verify flag is gone using list_project_flags with feature_name
        get_args = ListFlagsArgs(feature_name="remove_test")
        result = await call_mcp_tool(client, "list_project_flags", get_args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        # When flag doesn't exist, value should be None
        assert response.get("value") is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "pattern,flags_to_set,expected_matches",
    [
        # Test workflow* pattern - matches workflow, workflow-file, workflow-consent
        (
            "workflow*",
            [
                ("workflow", True),
                ("workflow-file", ".workflow.yaml"),
                ("workflow-consent", True),
                ("openspec", True),
            ],
            ["workflow", "workflow-file", "workflow-consent"],
        ),
        # Test content-* pattern - matches content-format, content-style
        (
            "content-*",
            [("content-format", "mime"), ("content-style", "plain"), ("workflow", True)],
            ["content-format", "content-style"],
        ),
        # Test *spec pattern
        ("*spec", [("openspec", True), ("workflow", True)], ["openspec"]),
        # Test pattern with no matches
        ("nonexistent*", [("workflow", True), ("openspec", True)], []),
    ],
    ids=["workflow-prefix", "content-prefix", "spec-suffix", "no-matches"],
)
async def test_list_flags_with_glob_pattern(
    mcp_server, test_session, monkeypatch, pattern, flags_to_set, expected_matches
):
    """Test listing flags with glob pattern filtering."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        # Set flags
        for flag_name, flag_value in flags_to_set:
            await call_mcp_tool(client, "set_project_flag", SetFlagArgs(feature_name=flag_name, value=flag_value))

        # Test pattern
        result = await call_mcp_tool(client, "list_project_flags", ListFlagsArgs(feature_name=pattern))
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert isinstance(response["value"], dict)

        # Check expected matches
        for expected in expected_matches:
            assert expected in response["value"], f"Expected {expected} in {response['value']}"

        # Check no unexpected matches
        assert len(response["value"]) == len(expected_matches), (
            f"Expected {len(expected_matches)} matches, got {len(response['value'])}: {response['value']}"
        )


@pytest.mark.anyio
async def test_list_flags_exact_match_returns_single_value(mcp_server, test_session, monkeypatch):
    """Test that exact match (no wildcards) returns single value, not dict."""
    monkeypatch.setenv("PWD", "/fake/path/test")

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        # Set a flag
        await call_mcp_tool(client, "set_project_flag", SetFlagArgs(feature_name="workflow", value=True))

        # Test exact match returns single value
        result = await call_mcp_tool(client, "list_project_flags", ListFlagsArgs(feature_name="workflow"))
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert response["value"] is True  # Single value, not dict
        assert not isinstance(response["value"], dict)
