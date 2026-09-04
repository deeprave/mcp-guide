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
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    application = create_application(ServerConfig(configdir=str(config_dir)))

    async with Client(application.server, mode="2026-07-28") as client:
        bound = await client.call_tool(initial["name"], initial["arguments"])
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        continuation["arguments"]["args"]["session_id"] = session_id
        resumed = await client.call_tool(continuation["name"], continuation["arguments"])
        with pytest.raises(ToolError, match="invalid_session"):
            await client.call_tool(
                continuation["name"],
                {"args": {"session_id": "00000000-0000-4000-8000-000000000000"}},
            )
        with pytest.raises(ToolError, match="invalid_session"):
            await client.call_tool(
                continuation["name"],
                {"args": {"session_id": "bad\x00id"}},
            )

    assert resumed.structured_content is not None
    assert resumed.structured_content["success"] is True
    assert resumed.structured_content["value"]["project"] == "fixture-project"


@pytest.mark.anyio
async def test_prompt_and_resource_boundaries_handle_invalid_and_unbound_sessions(tmp_path, monkeypatch) -> None:
    """Prompt and resource adapters return Guide's invalid_session result, not a protocol error."""
    import importlib

    from fastmcp import Client
    from fastmcp.exceptions import ToolError

    import mcp_guide.prompts.guide_prompt as guide_prompt_module
    import mcp_guide.resources as resources_module
    from mcp_guide.cli import ServerConfig
    from mcp_guide.core.prompt_decorator import _PROMPT_REGISTRY
    from mcp_guide.core.resource_decorator import _RESOURCE_REGISTRY
    from mcp_guide.server import create_application

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    monkeypatch.setenv("MCP_PROMPT_NAME", "guide")
    if "guide" not in _PROMPT_REGISTRY:
        importlib.reload(guide_prompt_module)
    if not _RESOURCE_REGISTRY:
        importlib.reload(resources_module)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    application = create_application(ServerConfig(configdir=str(config_dir)))

    async with Client(application.server, mode="2026-07-28") as client:
        unbound_prompt = await client.get_prompt("guide", {"arg1": "docs"})
        with pytest.raises(ToolError, match="no_project"):
            await client.call_tool("read_resource", {"args": {"uri": "guide://docs"}})
        stale_prompt = await client.get_prompt("guide", {"session_id": "00000000-0000-4000-8000-000000000000"})
        stale_resource = await client.read_resource("guide://_help?session_id=00000000-0000-4000-8000-000000000000")

    def payload_text(result) -> str:
        messages = getattr(result, "messages", None) or getattr(result, "contents", None) or [result]
        first = messages[0]
        content = getattr(first, "content", first)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return str(content[0])
        return str(getattr(content, "text", content))

    def payload_json(result) -> dict:
        text = payload_text(result)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            pytest.fail(f"expected JSON Guide payload, got: {text!r}")
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pytest.fail(f"expected JSON Guide payload, got: {text!r}")

    assert payload_json(stale_prompt)["error_type"] == "invalid_session"
    assert payload_json(stale_resource)["error_type"] == "invalid_session"
    assert payload_json(unbound_prompt)["error_type"] == "no_project"
