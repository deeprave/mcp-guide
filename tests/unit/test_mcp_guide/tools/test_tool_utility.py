"""Tests for utility tools."""

from types import SimpleNamespace

import pytest

from mcp_guide.agent_detection import AgentInfo, detect_agent
from mcp_guide.mcp_context import SessionProtocolType
from mcp_guide.tools.tool_utility import GetClientInfoArgs, internal_client_info


def _make_request_context(agent_info=None, client_params=None, protocol_type=SessionProtocolType.LEGACY):
    """Build an explicit application context with a resolved Session."""
    session = SimpleNamespace(agent_info=agent_info, client_params=client_params, protocol_type=protocol_type)
    return SimpleNamespace(session=session), session


@pytest.mark.anyio
async def test_client_info_formats_agent_cached_at_the_boundary():
    """Test client_info formats agent information already cached by the boundary."""
    request_context, _session = _make_request_context(
        agent_info=detect_agent({"clientInfo": {"name": "Kiro CLI", "version": "1.0.0"}}),
    )
    result = await internal_client_info(GetClientInfoArgs(), request_context)

    assert result.success is True
    assert result.value["agent"] == "Kiro CLI"
    assert result.value["normalized_name"] == "q-dev"
    assert result.value["version"] == "1.0.0"
    assert result.value["command_prefix"] == "@"
    assert "Kiro CLI" in result.message


@pytest.mark.anyio
async def test_client_info_with_cache():
    """Test client_info returns session-cached agent info."""
    cached = AgentInfo(name="Cached Agent", normalized_name="cached", version="2.0.0", prompt_prefix="/")
    request_context, _session = _make_request_context(
        agent_info=cached,
        client_params={"clientInfo": {"name": "Different Agent", "version": "3.0.0"}},
    )

    result = await internal_client_info(GetClientInfoArgs(), request_context)

    assert result.success is True
    assert result.value["agent"] == "Cached Agent"
    assert result.value["version"] == "2.0.0"
    assert "Different Agent" not in result.message


@pytest.mark.anyio
async def test_client_info_no_client_params():
    """Test client_info handles missing client_params."""
    request_context, _session = _make_request_context(agent_info=None, client_params=None)
    result = await internal_client_info(GetClientInfoArgs(), request_context)

    assert result.success is False
    assert "No client information available" in result.error


@pytest.mark.anyio
async def test_client_info_returns_failure_without_protocol_information():
    """Client information fails rather than asserting without a protocol class."""
    request_context, _session = _make_request_context(
        agent_info=detect_agent({"clientInfo": {"name": "Cursor", "version": "1.0.0"}}),
        protocol_type=None,
    )

    result = await internal_client_info(GetClientInfoArgs(), request_context)

    assert result.success is False
    assert result.error == "No protocol information available"


@pytest.mark.anyio
async def test_client_info_dict_without_client_info():
    """Test client_info with dict missing clientInfo."""
    request_context, _session = _make_request_context(agent_info=detect_agent({}), client_params={})
    result = await internal_client_info(GetClientInfoArgs(), request_context)

    assert result.success is True
    assert result.value["agent"] == "Unknown"
    assert result.value["normalized_name"] == "unknown"
    assert result.value["command_prefix"] is None


@pytest.mark.anyio
async def test_client_info_codex_reports_no_command_prefix():
    """Test client_info reports no prompt prefix for Codex."""
    request_context, _session = _make_request_context(
        agent_info=detect_agent({"clientInfo": {"name": "codex-mcp-client", "version": "0.116.0"}}),
    )
    result = await internal_client_info(GetClientInfoArgs(), request_context)

    assert result.success is True
    assert result.value["agent"] == "codex-mcp-client"
    assert result.value["normalized_name"] == "codex"
    assert result.value["command_prefix"] is None
    assert "Command Prefix: None" in result.message


@pytest.mark.anyio
async def test_client_info_formats_modern_metadata_cached_at_boundary():
    """Modern request metadata is already cached before application dispatch."""
    client_params = {"clientInfo": {"name": "Cursor", "version": "1.0.0"}}
    request_context, session = _make_request_context(
        agent_info=detect_agent(client_params), client_params=client_params
    )
    result = await internal_client_info(GetClientInfoArgs(), request_context)
    assert result.success is True
    assert result.value["agent"] == "Cursor"
    assert session.client_params == client_params


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("protocol_type", "expected_protocol"),
    [
        (SessionProtocolType.MCP_2026_07_28, "MCP 2026-07-28"),
        (SessionProtocolType.LEGACY, "legacy"),
    ],
)
async def test_client_info_returns_the_established_protocol_classification(protocol_type, expected_protocol):
    """The client-information tool reports the connection's public protocol class."""
    request_context, _session = _make_request_context(
        agent_info=detect_agent({"clientInfo": {"name": "Cursor", "version": "1.0.0"}}),
        protocol_type=protocol_type,
    )

    result = await internal_client_info(GetClientInfoArgs(), request_context)

    assert result.success is True
    assert result.value["protocol"] == expected_protocol
    assert f"Protocol: {expected_protocol}" in result.message
