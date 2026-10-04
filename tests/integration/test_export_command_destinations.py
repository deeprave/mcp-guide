"""Export command routes reject unsafe destinations before returning guidance."""

import json
from typing import Any
from urllib.parse import quote

import pytest

from mcp_guide.prompts.guide_prompt import guide
from mcp_guide.result_constants import ERROR_SECURITY
from mcp_guide.runtime import RequestContext
from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource


@pytest.fixture
def export_command_project(resource_project: RequestContext) -> RequestContext:
    commands = resource_project.resolve_document_path("_commands/export")
    commands.mkdir()
    (commands / "add.mustache").write_text("---\naliases: [export]\nminargs: 2\n---\n{{args.1.value}}")
    return resource_project


async def invoke_export_command(context: RequestContext, route: str, destination: str) -> dict[str, Any]:
    command = "export" if route.endswith("alias") else "export/add"
    if route.startswith("prompt"):
        result = await guide.__wrapped__(f":{command}", "docs", destination, request_context=context)
        return json.loads(result.messages[0].content.text)
    result = await internal_read_resource(
        ReadResourceArgs(uri=f"guide://_{command}/docs/{quote(destination, safe='')}", session_id=context.session_id),
        context,
    )
    return result.to_json()


@pytest.mark.anyio
@pytest.mark.parametrize("route", ["prompt", "prompt-alias", "resource", "resource-alias"])
@pytest.mark.parametrize("character", ["\x00", "\t", "\n", "\r", "\x7f", "`"])
async def test_command_destination_rejected_without_rendering_or_echoing(export_command_project, route, character):
    destination = f"exports/file.md{character}INJECTED_INSTRUCTION"
    payload = await invoke_export_command(export_command_project, route, destination)

    assert payload["success"] is False
    assert payload["error_type"] == ERROR_SECURITY
    assert payload["error"] == "Export destination is invalid or outside configured write paths"
    assert "INJECTED_INSTRUCTION" not in json.dumps(payload)


@pytest.mark.anyio
@pytest.mark.parametrize("route", ["prompt", "prompt-alias", "resource", "resource-alias"])
@pytest.mark.parametrize(
    "destination,expected",
    [("exports/report.md", "exports/report.md"), ("exports\\report.md", "exports/report.md")],
)
async def test_command_guidance_uses_canonical_destination(export_command_project, route, destination, expected):
    payload = await invoke_export_command(export_command_project, route, destination)

    assert payload["success"] is True
    assert payload["value"] == expected
