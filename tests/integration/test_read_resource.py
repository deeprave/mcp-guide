"""Resource URI routing through real project content and command templates."""

import pytest

from mcp_guide.result_constants import (
    AGENT_INFO,
    INSTRUCTION_AGENT_INFORMATION,
    INSTRUCTION_DISPLAY_ONLY,
    USER_INFO,
)
from mcp_guide.tools.tool_resource import ListSkillsArgs, ReadResourceArgs, internal_read_resource, list_skills


@pytest.mark.anyio
@pytest.mark.parametrize(
    "uri,expected",
    [
        ("guide://docs", "docs content"),
        ("guide://docs/readme", "docs content"),
        ("guide://_project", "resource-project verbose"),
        ("guide://_openspec/show/my-change?verbose=true", "Show my-change verbose"),
        ("guide://_project?table=true", "resource-project verbose table"),
        (
            "guide://$workflow-status?session_id=resource-session",
            "Read the current Guide workflow and OpenSpec status.",
        ),
    ],
)
async def test_resource_uri_renders_the_bound_projects_content(resource_project, uri, expected):
    result = await internal_read_resource(ReadResourceArgs(uri=uri), resource_project)
    assert result.success, result.error
    assert result.value == expected


@pytest.mark.anyio
async def test_skill_entrypoint_reports_its_rendered_virtual_file(resource_project):
    """A skill entrypoint reports the public SKILL.md path rather than its source template."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$workflow-status"), resource_project)

    assert result.success, result.error
    assert result.message == "Rendered skill file: workflow-status/SKILL.md"
    assert result.value == "Read the current Guide workflow and OpenSpec status."


@pytest.mark.anyio
async def test_skill_elicitation_renders_the_declared_non_elicitation_fallback(resource_project):
    """A skill may render instructions when a caller cannot complete its declared form."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$workflow-review"), resource_project)

    assert result.success, result.error
    assert result.message == "Rendered skill file: workflow-review/SKILL.md"
    assert result.value == "Review "


@pytest.mark.anyio
async def test_skill_package_member_receives_the_package_context(resource_project):
    """A requested member receives public package URIs and reports its virtual path."""
    result = await internal_read_resource(
        ReadResourceArgs(uri="guide://$workflow-status/resources/checklist.md?mode=summary"), resource_project
    )

    assert result.success, result.error
    assert result.message == "Rendered skill file: workflow-status/resources/checklist.md"
    assert result.value == ("Package=workflow-status; resources=guide://$workflow-status/resources; mode=summary")


@pytest.mark.anyio
async def test_skill_script_is_retrieved_as_content_without_server_execution(resource_project):
    """A package script is a readable member, never a Guide server action."""
    result = await internal_read_resource(
        ReadResourceArgs(uri="guide://$workflow-status/scripts/inspect.py"), resource_project
    )

    assert result.success, result.error
    assert result.message == "Rendered skill file: workflow-status/scripts/inspect.py"
    assert result.value == "print('inspect locally')\n"


@pytest.mark.anyio
async def test_skill_member_cannot_escape_its_package(resource_project):
    """Traversal cannot read a sibling package or an arbitrary skills-root member."""
    result = await internal_read_resource(
        ReadResourceArgs(uri="guide://$workflow-status/resources/%2E%2E/%2E%2E/SKILL.md"), resource_project
    )

    assert result.success is False
    assert result.error_type == "validation_error"
    assert result.error == "Guide skill member path must remain within its package"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "member",
    [
        "resources/*.md",
        "resources/**/checklist.md",
        "resources/%3F.md",
        "resources/[a-z].md",
    ],
)
async def test_skill_member_rejects_glob_syntax(resource_project, member):
    """Skill package members are literal paths, never document glob patterns."""
    result = await internal_read_resource(ReadResourceArgs(uri=f"guide://$workflow-status/{member}"), resource_project)

    assert result.success is False
    assert result.error_type == "validation_error"
    assert result.error == "Guide skill member path must not contain glob syntax"


@pytest.mark.anyio
async def test_missing_skill_member_is_a_structured_not_found_result(resource_project):
    """An unavailable package member does not escape as a renderer exception."""
    result = await internal_read_resource(
        ReadResourceArgs(uri="guide://$workflow-status/resources/missing.md"), resource_project
    )

    assert result.success is False
    assert result.error_type == "not_found"


@pytest.mark.anyio
async def test_invalid_skill_catalogue_query_is_a_structured_validation_result(resource_project):
    """Skill catalogue URI arguments use the standard Guide validation envelope."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$?verbose=maybe"), resource_project)

    assert result.success is False
    assert result.error_type == "validation_error"


@pytest.mark.anyio
async def test_skill_catalogue_is_available_through_read_resource(resource_project):
    """The client-facing resource tool exposes the server-owned skills catalogue."""
    incomplete_skill = resource_project.resolve_document_path("_skills/missing-usage/SKILL.md.mustache")
    incomplete_skill.parent.mkdir(parents=True)
    incomplete_skill.write_text(
        "---\nname: missing-usage\ndescription: Must not appear without catalogue usage guidance.\n---\nIgnored."
    )

    result = await internal_read_resource(ReadResourceArgs(uri="guide://$"), resource_project)

    assert result.success, result.error
    assert "workflow-status" in result.value
    assert "grouped/nested" not in result.value
    assert "missing-usage" not in result.value
    assert "Use when: Use when the user asks for the current Guide workflow or OpenSpec status." in result.value
    assert result.disposition == AGENT_INFO
    assert result.instruction == INSTRUCTION_AGENT_INFORMATION


@pytest.mark.anyio
async def test_verbose_skill_catalogue_is_user_information_through_read_resource(resource_project):
    """A skill URI query reaches the catalogue loader unchanged."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$?verbose=true"), resource_project)

    assert result.success, result.error
    assert "workflow-status" in result.value
    assert result.disposition == USER_INFO
    assert result.instruction == INSTRUCTION_DISPLAY_ONLY


@pytest.mark.anyio
async def test_table_skill_catalogue_is_user_information_through_read_resource(resource_project):
    """A valueless table query produces a user-facing Markdown table through guide://$."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$?table"), resource_project)

    assert result.success, result.error
    assert result.value.startswith("| Skill | Purpose | Use when | Entrypoint |")
    assert "| `workflow-status` |" in result.value
    assert "| Use when the user asks for the current Guide workflow or OpenSpec status. |" in result.value
    assert "`guide://$workflow-status`" in result.value
    assert result.disposition == USER_INFO
    assert result.instruction == INSTRUCTION_DISPLAY_ONLY


@pytest.mark.anyio
async def test_list_skills_is_a_registered_agent_information_tool(resource_project):
    """The direct skill catalogue follows the normal Guide tool response path."""
    response = await list_skills.__wrapped__(ListSkillsArgs(), resource_project)
    payload = response.structured_content

    assert payload["success"] is True
    assert "workflow-status" in payload["value"]
    assert payload["disposition"] == AGENT_INFO
    assert payload["instruction"].startswith(INSTRUCTION_AGENT_INFORMATION)


@pytest.mark.anyio
async def test_list_skills_verbose_returns_user_information(resource_project):
    """An explicit user-facing list is delivered rather than silently consumed."""
    response = await list_skills.__wrapped__(ListSkillsArgs(verbose=True), resource_project)
    payload = response.structured_content

    assert payload["success"] is True
    assert "workflow-status" in payload["value"]
    assert payload["disposition"] == USER_INFO
    assert payload["instruction"].startswith(INSTRUCTION_DISPLAY_ONLY)


@pytest.mark.anyio
async def test_list_skills_table_returns_a_user_facing_markdown_table(resource_project):
    """The direct tool has the same table representation as the resource URI."""
    response = await list_skills.__wrapped__(ListSkillsArgs(table=True), resource_project)
    payload = response.structured_content

    assert payload["success"] is True
    assert payload["value"].startswith("| Skill | Purpose | Use when | Entrypoint |")
    assert "| `workflow-status` |" in payload["value"]
    assert payload["disposition"] == USER_INFO
    assert payload["instruction"].startswith(INSTRUCTION_DISPLAY_ONLY)


@pytest.mark.anyio
async def test_nested_skill_package_is_not_discoverable(resource_project):
    """Guide skill packages are direct children so their names remain portable."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$grouped/nested"), resource_project)

    assert result.success is False
    assert result.error_type == "not_found"


@pytest.mark.anyio
async def test_invalid_scheme(resource_project):
    result = await internal_read_resource(ReadResourceArgs(uri="http://example.com"), resource_project)
    assert result.success is False
    assert result.error_type == "validation_error"
    assert "guide://" in result.error


@pytest.mark.anyio
async def test_read_resource_uri_session_id_resumes_bound_session(runtime, tmp_path) -> None:
    """A unique URI session_id selects the already-bound Session before scope."""
    from types import SimpleNamespace

    from mcp_guide.runtime import OwnerKey
    from mcp_guide.session import bind_session_project, request_context_scope

    session = runtime.resolve_session(OwnerKey("bound-session"))
    session.session_id = "bound-session"
    await bind_session_project(session, "/client/workspace/bound-session")
    runtime.retain_session(OwnerKey("bound-session"), session)

    args = ReadResourceArgs(uri="guide://docs?session_id=bound-session")
    assert args.session_id == "bound-session"

    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28",
            request_id="uri-resume",
            meta=None,
            lifespan_context=runtime,
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )
    async with request_context_scope(ctx, args.session_id, allow_pwd_bootstrap=False) as request_context:
        assert request_context.session is session
        assert request_context.session.project_is_bound is True
