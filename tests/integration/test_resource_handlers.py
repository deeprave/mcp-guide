"""Native resource responses from actual content and command routing."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from mcp_types import InputRequiredResult

from mcp_guide.resources import guide_command_resource, guide_resource, guide_skill_resource


@pytest.mark.anyio
async def test_command_resource_returns_and_resumes_declared_mcp_input(resource_project):
    """A command uses the shared resolver before it renders its body."""
    resource_project.resolve_document_path("_commands/project/project.mustache").write_text(
        "---\n"
        "aliases: ['project']\n"
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
        "{{#elicit.target}}Project {{kwargs.mode}}{{/elicit.target}}"
    )
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    pending = await guide_command_resource.__wrapped__(
        "project", request_context=resource_project, request_uri="guide://_project", mcp_context=context
    )

    assert isinstance(pending, InputRequiredResult)
    accepted = await guide_command_resource.__wrapped__(
        "project",
        request_context=resource_project,
        request_uri="guide://_project",
        mcp_context=SimpleNamespace(
            session=context.session,
            request_context=context.request_context,
            request_state=pending.request_state,
            input_responses={"target": SimpleNamespace(action="accept", content={"mode": "branch"})},
        ),
    )
    payload = json.loads(accepted.contents[0].content)

    assert payload["success"] is True
    assert payload["value"] == "Project branch"


@pytest.mark.anyio
async def test_command_logs_a_missing_listed_partial_without_parent_elicitation(resource_project, caplog):
    """A missing listed contributor does not turn an otherwise valid command into a client failure."""
    command_dir = resource_project.resolve_document_path("_commands/project")
    (command_dir / "project.mustache").write_text(
        "---\naliases: ['project']\nincludes: ['missing-input']\n---\nProject"
    )

    result = await guide_command_resource.__wrapped__(
        "project", request_context=resource_project, request_uri="guide://_project"
    )
    payload = json.loads(result.contents[0].content)

    assert payload["success"] is True
    assert any("Partial template not found" in record.message for record in caplog.records)


@pytest.mark.anyio
async def test_unlisted_inline_partial_does_not_request_input(resource_project, modern_elicitation_context):
    """Only frontmatter-listed partials can contribute pre-render input forms."""
    command_dir = resource_project.resolve_document_path("_commands/project")
    (command_dir / "project.mustache").write_text("---\naliases: ['project']\n---\nProject {{>input}}")
    (command_dir / "_input.mustache").write_text(
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
        "inline"
    )

    result = await guide_command_resource.__wrapped__(
        "project",
        request_context=resource_project,
        request_uri="guide://_project",
        mcp_context=modern_elicitation_context(),
    )

    assert not isinstance(result, InputRequiredResult)


@pytest.mark.anyio
async def test_unknown_skill_has_a_clear_not_found_response(resource_project):
    missing = await guide_skill_resource.__wrapped__("unknown", request_context=resource_project, request_uri=None)
    payload = json.loads(missing.contents[0].content)

    assert payload["success"] is False
    assert payload["error_type"] == "not_found"
    assert payload["error"] == "Guide skill 'unknown' was not found"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "exception,expected",
    [
        (ValueError("Invalid value"), "Invalid value"),
        (FileNotFoundError("File not found"), "File not found"),
        (PermissionError("Permission denied"), "Permission denied"),
        (Exception("Unexpected error"), "Unexpected error: Unexpected error"),
    ],
)
@pytest.mark.slow
async def test_resource_serialises_propagated_errors(resource_project, exception, expected):
    # Inject propagated failures deterministically; normal content errors become Results before this boundary.
    with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=exception)):
        result = await guide_resource.__wrapped__("docs", "readme", request_context=resource_project, request_uri=None)
    payload = json.loads(result.contents[0].content)
    assert payload["success"] is False
    assert payload["error"] == expected
