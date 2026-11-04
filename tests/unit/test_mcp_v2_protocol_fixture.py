"""MCP v2 compatibility behaviour tests."""

import json

import pytest


@pytest.mark.anyio
async def test_mcp_v2_arguments_execute_against_the_modern_fastmcp_surface(tmp_path, monkeypatch) -> None:
    """Nested arguments bind and resume one modern interaction."""
    from fastmcp import Client
    from fastmcp.exceptions import ToolError

    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    initial = {
        "name": "set_project",
        "arguments": {"args": {"path": str(tmp_path / "fixture-project")}},
    }
    continuation = {
        "name": "get_project",
        "arguments": {"args": {"session_id": "<fastmcp-session-id>"}},
    }
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
async def test_prompt_debug_log_describes_arguments_without_their_text(tmp_path, monkeypatch, caplog) -> None:
    """User-supplied prompt arguments must not be written to DEBUG logs."""
    import logging

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
    (docroot / "_commands" / "project.mustache").write_text("{{project.name}}", encoding="utf-8")
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    sensitive = "private-value-4711"

    async with Client(application.server, mode="2026-07-28") as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        with caplog.at_level(logging.DEBUG, logger="mcp_guide.prompts.guide_prompt"):
            await client.get_prompt(
                "guide", {"arg1": "_project", "arg2": sensitive, "session_id": bound.structured_content["session_id"]}
            )

    invoked = [record.getMessage() for record in caplog.records if "invoked" in record.getMessage()]
    assert invoked
    assert all(sensitive not in message for message in invoked)
    assert any("2 argument(s)" in message for message in invoked)


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
@pytest.mark.parametrize(
    ("argv", "asked", "rendered"),
    [
        ([":pick"], True, "name:{choice}"),
        ([":pick", "docs"], False, "arg:docs"),
        (["_pick?name=docs"], False, "name:docs"),
    ],
    ids=["asks", "positional-supplies", "keyword-supplies"],
)
async def test_command_offers_project_categories_unless_the_value_is_already_supplied(
    tmp_path, monkeypatch, mode, argv, asked, rendered
) -> None:
    """A sourced form reaches the client with the project's categories only when no value was supplied."""
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
    (docroot / "_commands" / "pick.mustache").write_text(
        "---\n"
        "elicitation:\n"
        "  choose:\n"
        "    message: Choose a category.\n"
        "    fallback: render\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        name: {type: string, source: project-categories}\n"
        "      required: [name]\n"
        "---\n"
        "{{#args.0.value}}arg:{{args.0.value}}{{/args.0.value}}"
        "{{^args.0.value}}name:{{kwargs.name}}{{/args.0.value}}",
        encoding="utf-8",
    )
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    offered: list[list[str]] = []

    async def choose_first(_message, _response_type, params, _context):
        schema = params.requested_schema["properties"]["name"]
        assert "source" not in schema
        offered.append(schema["enum"])
        return {"name": schema["enum"][0]}

    async with Client(application.server, mode=mode, elicitation_handler=choose_first) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        for category in ("docs", "code"):
            added = await client.call_tool(
                "category_collection_add",
                {
                    "args": {
                        "type": "category",
                        "name": category,
                        "dir": category,
                        "patterns": ["*.md"],
                        "session_id": session_id,
                    }
                },
            )
            assert added.structured_content is not None and added.structured_content["success"] is True
        prompt_args = {f"arg{index}": value for index, value in enumerate(argv, start=1)}
        prompt = await client.get_prompt("guide", {**prompt_args, "session_id": session_id})

    payload = json.loads(prompt.messages[0].content.text)
    assert payload["success"] is True
    assert bool(offered) is asked
    if asked:
        assert len(offered) == 1
        assert {"docs", "code"} <= set(offered[0])
    assert payload["value"] == rendered.format(choice=offered[0][0] if offered else "")


@pytest.mark.anyio
async def test_registered_mcp_prompt_drives_modern_command_elicitation(tmp_path, monkeypatch) -> None:
    """The registered prompt transports a modern elicitation round trip."""
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
    (docroot / "_commands" / "review.mustache").write_text(
        "---\n"
        "elicitation:\n"
        "  target:\n"
        "    message: Choose target.\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        mode:\n"
        "          type: string\n"
        "      required: [mode]\n"
        "---\n"
        "Review {{kwargs.mode}}",
        encoding="utf-8",
    )
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))

    async def select_target(*_args):
        return {"mode": "branch"}

    async with Client(
        application.server,
        mode="2026-07-28",
        elicitation_handler=select_target,
    ) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        prompt = await client.get_prompt("guide", {"arg1": ":review", "session_id": session_id})

    payload = json.loads(prompt.messages[0].content.text)
    assert payload["success"] is True
    assert payload["value"] == "Review branch"


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


def _create_fallback_skill_application(tmp_path, monkeypatch):
    """Create an application whose skill asks for a target and renders its own fallback guidance."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  guide-development: true\n", encoding="utf-8")
    (docroot / "_skills" / "fallback-review").mkdir(parents=True)
    (docroot / "_skills" / "fallback-review" / "SKILL.md.mustache").write_text(
        "---\n"
        "name: fallback-review\n"
        "description: Review the selected target.\n"
        "usage: Use when the user requests a review.\n"
        "elicitation:\n"
        "  review-target:\n"
        "    message: Choose the target for this review.\n"
        "    fallback: render\n"
        "    schema:\n"
        "      type: object\n"
        "      title: Review target\n"
        "      description: Extra keys that strict clients reject.\n"
        "      properties:\n"
        "        mode:\n"
        "          type: string\n"
        "          title: Mode\n"
        "          enum: [uncommitted, main]\n"
        "        verbose:\n"
        "          type: boolean\n"
        "      required: [mode]\n"
        "---\n"
        "{{#kwargs.mode}}Review {{kwargs.mode}}{{/kwargs.mode}}{{^kwargs.mode}}Ask the user for a target{{/kwargs.mode}}\n",
        encoding="utf-8",
    )
    return create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))


async def _read_skill_with_handler(application, project_root, handler, mode, uri="guide://$fallback-review"):
    """Bind a project and read the fixture skill through a client that answers with the handler."""
    from fastmcp import Client

    async with Client(application.server, mode=mode, elicitation_handler=handler) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        args = {"uri": uri}
        if mode != "legacy":
            args["session_id"] = bound.structured_content["session_id"]
        return await client.call_tool("read_resource", {"args": args}, raise_on_error=False)


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
async def test_client_that_declines_the_form_gets_the_skills_fallback_guidance(tmp_path, monkeypatch, mode) -> None:
    """A decline, as sent by Claude Code and Codex for agent-initiated calls, renders instead of failing."""
    from fastmcp.client.elicitation import ElicitResult

    application = _create_fallback_skill_application(tmp_path, monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    requested = []

    async def decline(message, response_type, params, context):
        requested.append(params.requested_schema["properties"]["mode"]["enum"])
        return ElicitResult(action="decline")

    result = await _read_skill_with_handler(application, project_root, decline, mode)

    assert requested == [["uncommitted", "main"]]
    assert result.structured_content is not None
    assert result.structured_content["success"] is True
    assert result.structured_content["value"].strip() == "Ask the user for a target"


@pytest.mark.anyio
async def test_legacy_client_that_never_answers_gets_the_skills_fallback_guidance(tmp_path, monkeypatch) -> None:
    """A legacy client that leaves the request unanswered must not stall the call."""
    import anyio

    monkeypatch.setattr("mcp_guide.elicitation.elicitation_timeout_seconds", lambda: 0.2)
    application = _create_fallback_skill_application(tmp_path, monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()

    async def never_answers(message, response_type, params, context):
        await anyio.sleep(30)

    with anyio.fail_after(15):
        result = await _read_skill_with_handler(application, project_root, never_answers, "legacy")

    assert result.structured_content is not None
    assert result.structured_content["success"] is True
    assert result.structured_content["value"].strip() == "Ask the user for a target"


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
async def test_form_schema_sent_to_clients_uses_only_the_mcp_form_subset(tmp_path, monkeypatch, mode) -> None:
    """Strict clients such as Codex reject any form-schema key outside the MCP-defined subset."""
    from fastmcp.client.elicitation import ElicitResult

    application = _create_fallback_skill_application(tmp_path, monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    delivered = []

    async def decline(message, response_type, params, context):
        delivered.append(params.requested_schema)
        return ElicitResult(action="decline")

    await _read_skill_with_handler(application, project_root, decline, mode)

    assert len(delivered) == 1
    assert set(delivered[0]) <= {"$schema", "type", "properties", "required"}
    assert set(delivered[0]["properties"]) == {"mode", "verbose"}
    for definition in delivered[0]["properties"].values():
        assert set(definition) <= {"type", "enum", "description", "default", "minimum", "maximum", "pattern"}


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
async def test_uri_values_satisfying_every_form_render_identically_without_asking(tmp_path, monkeypatch, mode) -> None:
    """Supplying the form's keywords in the URI renders the same text on both protocols and asks nothing."""
    from fastmcp.client.elicitation import ElicitResult

    application = _create_fallback_skill_application(tmp_path, monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    asked = []

    async def record(message, response_type, params, context):
        asked.append(message)
        return ElicitResult(action="decline")

    result = await _read_skill_with_handler(
        application, project_root, record, mode, uri="guide://$fallback-review?mode=main"
    )

    assert asked == []
    assert result.structured_content is not None
    assert result.structured_content["success"] is True
    assert result.structured_content["value"].strip() == "Review main"
