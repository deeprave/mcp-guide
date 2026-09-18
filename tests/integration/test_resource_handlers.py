"""Native resource responses from actual content and command routing."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from mcp_types import InputRequiredResult

from mcp_guide.resources import guide_command_resource, guide_resource, guide_skill_resource, guide_skills_catalog
from mcp_guide.result_constants import USER_INFO


@pytest.mark.anyio
async def test_content_resource_uses_bound_project_and_policy_subpaths(resource_project):
    async def read(category, document):
        result = await guide_resource.__wrapped__(
            category, document, request_context=resource_project, request_uri=None
        )
        payload = json.loads(result.contents[0].content)
        assert payload["success"] is True
        assert payload["session_id"] == "resource-session"
        return payload["value"]

    assert await read("docs", "readme") == "docs content"
    assert await read("docs", "") == "docs content"
    assert await read("policies", "git/ops") == "git policy"


@pytest.mark.anyio
async def test_command_resource_preserves_query_aliases_and_failure(resource_project):
    result = await guide_command_resource.__wrapped__(
        "project", request_context=resource_project, request_uri="guide://_project?table=true"
    )
    payload = json.loads(result.contents[0].content)
    assert payload["success"] is True
    assert payload["session_id"] == "resource-session"
    assert payload["value"] == "resource-project verbose table"

    missing = await guide_command_resource.__wrapped__("unknown", request_context=resource_project, request_uri=None)
    payload = json.loads(missing.contents[0].content)
    assert payload["success"] is False
    assert "unknown" in payload["error"]


@pytest.mark.anyio
async def test_generic_resource_preserves_an_already_complete_command_uri(resource_project):
    """The generic command route does not append an already represented document path."""
    response = await guide_resource.__wrapped__(
        "_openspec",
        "show/my-change",
        request_context=resource_project,
        request_uri="guide://_openspec/show/my-change",
    )
    payload = json.loads(response.contents[0].content)

    assert payload["success"] is True
    assert payload["value"] == "Show my-change"


@pytest.mark.anyio
async def test_document_resource_exposes_cache_metadata_but_command_resource_does_not(resource_project):
    """Only non-command Guide resources expose a document cache policy."""
    resource_project.resolve_document_path("docs/readme.md").write_text("---\ncache: long\n---\ndocs content")

    document = await guide_resource.__wrapped__("docs", "readme", request_context=resource_project, request_uri=None)
    command = await guide_command_resource.__wrapped__("project", request_context=resource_project, request_uri=None)

    assert document.meta == {"mcp-guide": {"cache": {"ttl_ms": 86_400_000, "scope": "public"}}}
    assert command.meta is None


@pytest.mark.anyio
async def test_skill_catalogue_lists_each_frontmatter_defined_entrypoint(resource_project):
    """Skills are explicitly discoverable, then available at their advertised URI."""
    catalogue = await guide_skills_catalog.__wrapped__(request_context=resource_project, request_uri=None)
    catalogue_payload = json.loads(catalogue.contents[0].content)

    assert catalogue_payload["success"] is True
    assert "workflow-status" in catalogue_payload["value"]
    assert (
        "Use when: Use when the user asks for the current Guide workflow or OpenSpec status."
        in catalogue_payload["value"]
    )


@pytest.mark.anyio
async def test_verbose_skill_catalogue_resource_is_user_information(resource_project):
    """The resource entrypoint forwards its query option to the catalogue loader."""
    catalogue = await guide_skills_catalog.__wrapped__(
        request_context=resource_project,
        request_uri="guide://$?verbose=true",
        verbose=True,
    )
    catalogue_payload = json.loads(catalogue.contents[0].content)

    assert catalogue_payload["success"] is True
    assert catalogue_payload["disposition"] == USER_INFO
    assert "Report the current Guide workflow and OpenSpec status without changing it." in catalogue_payload["value"]
    assert "guide://$workflow-status" in catalogue_payload["value"]

    skill = await guide_skill_resource.__wrapped__(
        "workflow-status", request_context=resource_project, request_uri=None
    )
    skill_payload = json.loads(skill.contents[0].content)

    assert skill_payload["success"] is True
    assert skill_payload["value"] == "Read the current Guide workflow and OpenSpec status."
    assert skill_payload["message"] == "Rendered skill file: workflow-status/SKILL.md"
    assert skill_payload["disposition"] == "agent/instruction"

    routed = await guide_resource.__wrapped__(
        "$workflow-status", "", request_context=resource_project, request_uri="guide://$workflow-status"
    )
    routed_payload = json.loads(routed.contents[0].content)
    assert routed_payload["success"] is True
    assert routed_payload["value"] == "Read the current Guide workflow and OpenSpec status."


@pytest.mark.anyio
async def test_table_skill_catalogue_resource_is_user_information(resource_project):
    """The native resource handler preserves the table view query parameter."""
    catalogue = await guide_skills_catalog.__wrapped__(
        request_context=resource_project,
        request_uri="guide://$?table=true",
        table=True,
    )
    catalogue_payload = json.loads(catalogue.contents[0].content)

    assert catalogue_payload["success"] is True
    assert catalogue_payload["value"].startswith("| Skill | Purpose | Use when | Entrypoint |")
    assert catalogue_payload["disposition"] == USER_INFO


@pytest.mark.anyio
async def test_skill_resource_forwards_arbitrary_query_values_to_its_template(resource_project):
    """Skill templates receive URI keywords with command-equivalent semantics."""
    resource_project.resolve_document_path("_skills/workflow-status/SKILL.md.mustache").write_text(
        "---\n"
        "name: workflow-status\n"
        "description: Report the current Guide workflow and OpenSpec status without changing it.\n"
        "usage: Use when the user asks for the current Guide workflow or OpenSpec status.\n"
        "type: agent/instruction\n"
        "---\n"
        "Mode={{kwargs.mode}}; dry-run={{kwargs.dry_run}}"
    )

    skill = await guide_skill_resource.__wrapped__(
        "workflow-status",
        request_context=resource_project,
        request_uri="guide://$workflow-status?mode=summary&dry-run",
    )
    payload = json.loads(skill.contents[0].content)

    assert payload["success"] is True
    assert payload["value"] == "Mode=summary; dry-run=True"
    assert payload["message"] == "Rendered skill file: workflow-status/SKILL.md"


@pytest.mark.anyio
async def test_skill_frontmatter_requests_a_standard_mcp_selection(resource_project):
    """A modern resource read requests the selected skill's declared target form."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )
    result = await guide_skill_resource.__wrapped__(
        "workflow-review",
        request_context=resource_project,
        request_uri="guide://$workflow-review",
        mcp_context=context,
    )

    assert isinstance(result, InputRequiredResult)
    assert "review-target" in result.input_requests


@pytest.mark.anyio
async def test_skill_without_elicitation_renders_its_fallback_instructions(resource_project):
    """A render fallback lets the skill collect missing input from the user."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation=None))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await guide_skill_resource.__wrapped__(
        "workflow-review",
        request_context=resource_project,
        request_uri="guide://$workflow-review",
        mcp_context=context,
    )
    payload = json.loads(result.contents[0].content)

    assert payload["success"] is True
    assert payload["value"] == "Review "


@pytest.mark.anyio
async def test_workflow_review_uses_an_accepted_modern_selection(resource_project):
    """A modern retry renders the selected target through the existing URI contract."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"review-target": SimpleNamespace(action="accept", content={"mode": "main"})},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await guide_skill_resource.__wrapped__(
        "workflow-review/SKILL.md",
        request_context=resource_project,
        request_uri="guide://$workflow-review/SKILL.md",
        mcp_context=context,
    )
    payload = json.loads(result.contents[0].content)

    assert payload["success"] is True
    assert payload["value"] == "Review main"


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
async def test_resource_serialises_propagated_errors(resource_project, exception, expected):
    # Inject propagated failures deterministically; normal content errors become Results before this boundary.
    with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=exception)):
        result = await guide_resource.__wrapped__("docs", "readme", request_context=resource_project, request_uri=None)
    payload = json.loads(result.contents[0].content)
    assert payload["success"] is False
    assert payload["error"] == expected
