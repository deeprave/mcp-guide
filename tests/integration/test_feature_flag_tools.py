"""Integration tests for feature flag tools.

Tests feature flag tools through MCP protocol with real session management.
"""

import json

import pytest
from fastmcp.client import Client, FastMCPTransport

from mcp_guide.tools.tool_feature_flags import ListFeatureFlagsArgs, ListFlagsArgs, SetFeatureFlagArgs, SetFlagArgs
from mcp_guide.tools.tool_project import SetCurrentProjectArgs
from tests.conftest import call_mcp_tool


@pytest.mark.anyio
async def test_project_flag_lifecycle_via_mcp(mcp_server, test_session):
    """Set, list, select and remove a flag through the retained legacy protocol."""
    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(test_session)))
        assert bound.structured_content["success"] is True
        set_result = await call_mcp_tool(client, "set_project_flag", SetFlagArgs(feature_name="custom", value="value"))
        assert set_result.structured_content["success"] is True
        assert "custom" in set_result.structured_content["value"]

        listed = await call_mcp_tool(client, "list_project_flags", ListFlagsArgs())
        assert listed.structured_content["success"] is True
        assert listed.structured_content["value"]["custom"] == "value"
        selected = await call_mcp_tool(client, "list_project_flags", ListFlagsArgs(feature_name="custom"))
        assert selected.structured_content["success"] is True
        assert selected.structured_content["value"] == "value"

        removed = await call_mcp_tool(client, "set_project_flag", SetFlagArgs(feature_name="custom", value=None))
        assert removed.structured_content["success"] is True
        assert "removed" in removed.structured_content["value"].lower()
        absent = await call_mcp_tool(client, "list_project_flags", ListFlagsArgs(feature_name="custom"))
        assert absent.structured_content["success"] is True
        assert absent.structured_content.get("value") is None


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture
def mcp_server(mcp_server_factory):
    """Create a fresh MCP server per test for flag-tool isolation."""
    return mcp_server_factory(["tool_feature_flags", "tool_project"])


@pytest.fixture
def test_session(runtime, tmp_path):
    """Provide an absolute root; each client binds itself through the actual tool."""
    config = runtime.configuration_service().config_file
    config.write_text("feature_flags: {}\nprojects: {}\n")
    root = tmp_path / "flag-project"
    root.mkdir()
    return root


@pytest.mark.anyio
async def test_generic_project_flag_true_string_normalizes_to_boolean(mcp_server, test_session):
    """Test generic project flag string booleans normalize to real bools."""

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(test_session)))
        assert bound.structured_content["success"] is True
        await call_mcp_tool(client, "set_project_flag", SetFlagArgs(feature_name="custom-flag", value="true"))
        result = await call_mcp_tool(client, "list_project_flags", ListFlagsArgs(feature_name="custom-flag"))
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert response["value"] is True


@pytest.mark.anyio
async def test_generic_project_flag_rejects_structured_value(mcp_server, test_session):
    """Test generic project flags reject list values without explicit registration."""

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(test_session)))
        assert bound.structured_content["success"] is True
        result = await call_mcp_tool(
            client,
            "set_project_flag",
            SetFlagArgs(feature_name="custom-flag", value=["discussion"]),
        )
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "validation_error"


@pytest.mark.anyio
async def test_allow_client_info_global_flag_uses_shared_boolean_like_coercion(mcp_server, test_session):
    """Global allow-client-info should use the shared boolean-like coercion rules."""

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(test_session)))
        assert bound.structured_content["success"] is True
        await call_mcp_tool(
            client, "set_feature_flag", SetFeatureFlagArgs(feature_name="allow-client-info", value="no")
        )
        result = await call_mcp_tool(
            client, "list_feature_flags", ListFeatureFlagsArgs(feature_name="allow-client-info")
        )
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is True
        assert response["value"] is False


@pytest.mark.anyio
async def test_generic_global_flag_rejects_structured_value_as_validation_error(mcp_server, test_session):
    """Unsupported structured global flag values should surface as validation errors."""

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(test_session)))
        assert bound.structured_content["success"] is True
        result = await call_mcp_tool(
            client,
            "set_feature_flag",
            SetFeatureFlagArgs(feature_name="custom-flag", value=["discussion"]),
        )
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "validation_error"


@pytest.mark.anyio
async def test_flag_validation_via_mcp(mcp_server, test_session):
    """Test flag validation through MCP client."""

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(test_session)))
        assert bound.structured_content["success"] is True
        # Try to set flag with invalid name (contains period)
        args = SetFlagArgs(feature_name="invalid.flag", value=True)
        result = await call_mcp_tool(client, "set_project_flag", args)
        response = json.loads(result.content[0].text)  # type: ignore[union-attr]

        assert response["success"] is False
        assert response["error_type"] == "validation_error"
        assert "periods" in response["error"].lower()


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
async def test_list_flags_with_glob_pattern(mcp_server, test_session, pattern, flags_to_set, expected_matches):
    """Test listing flags with glob pattern filtering."""

    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(test_session)))
        assert bound.structured_content["success"] is True
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
