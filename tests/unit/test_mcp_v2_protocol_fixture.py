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
        unbound_status_prompt = await client.get_prompt("guide", {"arg1": ":status"})
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
    assert payload_json(unbound_status_prompt)["error_type"] == "no_project"


@pytest.mark.anyio
async def test_mcp_prompt_routes_explicit_command_and_skill_namespaces(tmp_path, monkeypatch) -> None:
    """Prompt retrieval routes underscore commands and dollar skills like Guide URIs."""
    from fastmcp import Client

    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir = tmp_path / "config"
    project_root.mkdir()
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(f"docroot: {docroot}\nprojects: {{}}\n", encoding="utf-8")
    (docroot / "_commands").mkdir(parents=True)
    (docroot / "_skills" / "workflow-status").mkdir(parents=True)
    (docroot / "_commands" / "project.mustache").write_text(
        "{{project.name}}{{#kwargs.verbose}} verbose{{/kwargs.verbose}}", encoding="utf-8"
    )
    (docroot / "_skills" / "workflow-status" / "SKILL.md.mustache").write_text(
        "---\n"
        "name: workflow-status\n"
        "description: Report workflow status.\n"
        "usage: Use when the user asks for workflow status.\n"
        "type: agent/instruction\n"
        "---\n"
        "Mode={{kwargs.mode}}",
        encoding="utf-8",
    )
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))

    async with Client(application.server, mode="2026-07-28") as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]

        command = await client.get_prompt("guide", {"arg1": "_project?verbose", "session_id": session_id})
        skill = await client.get_prompt("guide", {"arg1": "$workflow-status?mode=summary", "session_id": session_id})

    command_payload = json.loads(command.messages[0].content.text)
    skill_payload = json.loads(skill.messages[0].content.text)
    assert command_payload["value"] == "project verbose"
    assert skill_payload["value"] == "Mode=summary"


@pytest.mark.anyio
async def test_read_resource_drives_frontmatter_declared_skill_elicitation(tmp_path, monkeypatch) -> None:
    """The ordinary read_resource tool drives any skill's declared selection round trip."""
    from fastmcp import Client

    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  guide-development: true\n", encoding="utf-8")
    (docroot / "_skills" / "custom-review").mkdir(parents=True)
    (docroot / "_skills" / "custom-review" / "SKILL.md.mustache").write_text(
        "---\n"
        "name: custom-review\n"
        "description: Review the selected target.\n"
        "usage: Use when the user requests a review.\n"
        "elicitation:\n"
        "  review-target:\n"
        "    message: Choose the target for this review.\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        mode:\n"
        "          type: string\n"
        "          enum: [uncommitted, main, branch, pull-request]\n"
        "        reference:\n"
        "          type: string\n"
        "      required: [mode]\n"
        "---\n"
        "Review {{kwargs.mode}} {{kwargs.reference}}\n",
        encoding="utf-8",
    )
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))

    async def select_branch(*_args):
        return {"mode": "branch", "reference": "feature/example"}

    async with Client(
        application.server,
        mode="2026-07-28",
        elicitation_handler=select_branch,
    ) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        result = await client.call_tool(
            "read_resource",
            {"args": {"uri": "guide://$custom-review", "session_id": session_id}},
        )
        resource = await client.read_resource(f"guide://$custom-review?session_id={session_id}")

    assert result.structured_content is not None
    assert result.structured_content["success"] is True
    assert result.structured_content["value"] == "Review branch feature/example\n"
    assert resource[0].text is not None
    assert "Review branch feature/example" in resource[0].text
