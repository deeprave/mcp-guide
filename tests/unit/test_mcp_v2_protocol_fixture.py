"""Contract-fixture shape tests for the MCP v2 compatibility spike."""

import json
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "mcp_protocol" / "2026-07-28.json"


def test_mcp_v2_contract_fixture_covers_required_flows() -> None:
    """Keep the SDK spike's protocol acceptance matrix complete and parseable."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert fixture["protocolRevision"] == "2026-07-28"
    assert set(fixture["cases"]) == {
        "modern_discovery",
        "modern_tool",
        "modern_prompt",
        "modern_resource",
        "modern_request_state",
        "stdio",
        "streamable_http",
        "legacy_2025",
    }


def test_mcp_v2_contract_fixture_uses_json_rpc_messages() -> None:
    """Fixture requests are protocol messages, not framework-specific calls."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for case_name in ("modern_discovery", "legacy_2025"):
        for request in fixture["cases"][case_name]["requests"]:
            assert request["jsonrpc"] == "2.0"


def test_mcp_v2_fixture_uses_guide_nested_args_and_session_continuation() -> None:
    """The fixture records Guide's actual FastMCP tool contract, not stale request state."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    initial = fixture["cases"]["modern_request_state"]["initialRequest"]
    continuation = fixture["cases"]["modern_request_state"]["continuationRequest"]

    assert initial["params"]["arguments"] == {"args": {"path": "/client/workspace/demo"}}
    assert continuation["params"]["arguments"] == {"args": {"session_id": "<fastmcp-session-id>"}}
    assert "requestState" not in continuation["params"]


@pytest.mark.anyio
async def test_mcp_v2_fixture_arguments_execute_against_the_modern_fastmcp_surface(tmp_path, monkeypatch) -> None:
    """The fixture's nested arguments bind and resume one modern interaction."""
    from fastmcp import Client
    from fastmcp.exceptions import ToolError

    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    initial = fixture["cases"]["modern_request_state"]["initialRequest"]["params"]
    continuation = fixture["cases"]["modern_request_state"]["continuationRequest"]["params"]
    project_root = tmp_path / "fixture-project"
    project_root.mkdir()
    initial["arguments"]["args"]["path"] = str(project_root)
    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    application = create_application(ServerConfig(configdir=str(tmp_path / "config")))

    async with Client(application.server, mode="2026-07-28") as client:
        bound = await client.call_tool(initial["name"], initial["arguments"])
        assert bound.structured_content is not None
        session_id = bound.structured_content["value"]["session_id"]
        continuation["arguments"]["args"]["session_id"] = session_id
        resumed = await client.call_tool(continuation["name"], continuation["arguments"])
        with pytest.raises(ToolError, match="invalid_session"):
            await client.call_tool(
                continuation["name"],
                {"args": {"session_id": "00000000-0000-4000-8000-000000000000"}},
            )

    assert resumed.structured_content is not None
    assert resumed.structured_content["success"] is True
    assert resumed.structured_content["value"]["project"] == "fixture-project"
