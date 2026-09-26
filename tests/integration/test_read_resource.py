"""Resource URI routing through real project content and command templates."""

from types import SimpleNamespace

import pytest

from mcp_guide.core.tool_decorator import get_tool_registration
from mcp_guide.models import Category
from mcp_guide.render import rendering
from mcp_guide.render.recommendations import parse_recommendation
from mcp_guide.result_constants import (
    AGENT_INFO,
    INSTRUCTION_AGENT_INFORMATION,
    INSTRUCTION_DISPLAY_ONLY,
    USER_INFO,
)
from mcp_guide.tools.tool_resource import (
    ListSkillsArgs,
    ReadResourceArgs,
    UseSkillArgs,
    internal_read_resource,
    internal_use_skill,
    list_skills,
)


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
async def test_git_pr_triage_skill_is_available_for_analysis_only_review_feedback(resource_project):
    """A bundled triage skill delivers review analysis guidance without applying changes."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$git-pr-triage"), resource_project)

    assert result.success, result.error
    assert "analysis and recommendations only" in result.value
    assert "Do not modify pull-request code" in result.value
    recommendation = parse_recommendation("skill:just-one")
    assert f'Guide skill "just-one"[^{recommendation.label}]' in result.value


@pytest.mark.anyio
async def test_use_skill_shares_the_resource_skill_resolution(resource_project):
    result = await internal_use_skill("$workflow-status", resource_project, kwargs={})

    assert result.success, result.error
    assert result.value == "Read the current Guide workflow and OpenSpec status."


@pytest.mark.anyio
async def test_use_skill_rejects_member_paths(resource_project):
    result = await internal_use_skill("workflow-status/README.md", resource_project, kwargs={})

    assert not result.success
    assert result.error_type == "not_found"


@pytest.mark.anyio
async def test_use_skill_without_a_project_returns_standard_guidance(runtime):
    context = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="legacy", request_id="unbound-use-skill", meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )
    wrapper = get_tool_registration("use_skill").metadata.wrapped_func

    response = await wrapper(UseSkillArgs(skill="workflow-status"), ctx=context)

    assert response.structured_content["error_type"] == "no_project"


@pytest.mark.anyio
async def test_use_skill_tool_forwards_a_plain_name_and_arguments(resource_project):
    docroot = resource_project.resolve_document_path("")
    skill = docroot / "_skills/parsed-options/SKILL.md.mustache"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: parsed-options\ndescription: Render parsed skill options.\nusage: Use to inspect parsed options.\n---\n"
        "Mode={{kwargs.mode}}; verbose={{kwargs.verbose}}; pretty={{kwargs.pretty_print}}"
    )
    tool = get_tool_registration("use_skill").metadata.func
    result = await tool(
        UseSkillArgs(skill="$parsed-options", args=["mode=unrelenting", "verbose", "pretty-print"]),
        resource_project,
    )

    assert result.structured_content["success"] is True
    assert result.structured_content["value"] == "Mode=unrelenting; verbose=True; pretty=True"


@pytest.mark.anyio
async def test_skill_recommendation_delivers_a_fluent_reference_and_structured_detail(resource_project):
    docroot = resource_project.resolve_document_path("")
    skill = docroot / "_skills/custom-review/SKILL.md.mustache"
    skill.parent.mkdir(parents=True)
    command = docroot / "_commands/workflow/status.mustache"
    command.parent.mkdir(parents=True)
    command.write_text("---\ndescription: Render status.\n---\nStatus")
    skill.write_text(
        "---\nname: custom-review\ndescription: Review custom work.\nusage: Use for a custom review.\n---\n"
        "Next: {{#recommend}}skill:custom-review{{/recommend}}, then {{#recommend}}skill:custom-review{{/recommend}}. "
        "Read {{#recommend}}docs{{/recommend}}. "
        "Then {{#recommend}}command:workflow/status{{/recommend}}. "
        "Finally {{#recommend}}tool:get_content{{/recommend}}."
    )

    result = await internal_read_resource(ReadResourceArgs(uri="guide://$custom-review"), resource_project)

    assert result.success, result.error
    skill = parse_recommendation("skill:custom-review")
    content = parse_recommendation("docs")
    command = parse_recommendation("command:workflow/status")
    tool = parse_recommendation("tool:get_content")
    assert f'Guide skill "custom-review"[^{skill.label}]' in result.value
    assert result.value.count(f'Guide skill "custom-review"[^{skill.label}]') == 2
    assert f'Guide content "docs"[^{content.label}]' in result.value
    assert f'Guide command "workflow/status"[^{command.label}]' in result.value
    assert f'Guide tool "get_content"[^{tool.label}]' in result.value
    assert '"uri":"guide://$custom-review"' in result.value
    assert '"tool":"use_skill(\\"custom-review\\")"' in result.value
    assert '"uri":"guide://docs"' in result.value
    assert '"uri":"guide://_workflow/status"' in result.value
    assert '"tool":"get_content"' in result.value
    assert result.value.count(f"[^{skill.label}]:") == 1
    assert f"[^{skill.label}]:\n    ```json" in result.value


@pytest.mark.anyio
async def test_command_recommendation_preserves_its_force_option(resource_project):
    """A command recommendation remains directly actionable with its option."""
    docroot = resource_project.resolve_document_path("")
    archive = docroot / "_commands/openspec/archive.mustache"
    listing = docroot / "_commands/openspec/list.mustache"
    archive.write_text("After archive, use {{#recommend}}command:openspec/list?force{{/recommend}}.")
    listing.write_text("List changes")

    result = await internal_read_resource(ReadResourceArgs(uri="guide://_openspec/archive"), resource_project)

    assert result.success, result.error
    assert '"uri":"guide://_openspec/list?force"' in result.value


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("recommendation", "error"),
    [
        ("skill:does-not-exist", "Unknown recommended skill"),
        ("content:docs,missing", "Unknown recommended content"),
        ("skill:", "must name a target"),
        ("unknown:target", "Unknown recommendation type"),
    ],
)
async def test_recommendation_rejects_invalid_target_and_does_not_render(resource_project, recommendation, error):
    docroot = resource_project.resolve_document_path("")
    skill = docroot / "_skills/bad-recommendation/SKILL.md.mustache"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: bad-recommendation\ndescription: Broken recommendation.\nusage: Test invalid recommendations.\n---\n"
        f"{{{{#recommend}}}}{recommendation}{{{{/recommend}}}}"
    )

    result = await internal_read_resource(ReadResourceArgs(uri="guide://$bad-recommendation"), resource_project)

    assert not result.success
    assert error in result.error


@pytest.mark.anyio
async def test_git_skill_delivers_only_selected_policy_partials(resource_project):
    """A public Git skill includes the configured policy documents, and no others."""
    docroot = resource_project.resolve_document_path("")
    skill = docroot / "_skills/git-commit/SKILL.md.mustache"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\n"
        "name: git-commit\n"
        "description: Exercise Git policy delivery.\n"
        "usage: Use to exercise Git policy delivery.\n"
        "policies: [git/delivery, issue-tracking]\n"
        "---\n"
        "{{> git/delivery}}\n{{> issue-tracking}}"
    )
    for path, content in {
        "policies/git/delivery/branch.md": "selected-delivery",
        "policies/git/delivery/direct.md": "unselected-delivery",
        "policies/issue-tracking/linear.md": "selected-tracker",
        "policies/issue-tracking/jira.md": "unselected-tracker",
    }.items():
        document = docroot / path
        document.parent.mkdir(parents=True, exist_ok=True)
        document.write_text(content)

    await resource_project.session.update_config(
        lambda current: current.with_category(
            "policies",
            Category(
                dir="policies",
                patterns=["git/delivery/branch*", "issue-tracking/linear*"],
            ),
        )
    )

    result = await internal_read_resource(ReadResourceArgs(uri="guide://$git-commit"), resource_project)

    assert result.success, result.error
    assert "selected-delivery" in result.value
    assert "selected-tracker" in result.value
    assert "unselected-delivery" not in result.value
    assert "unselected-tracker" not in result.value


@pytest.mark.anyio
async def test_skill_render_failure_returns_a_structured_result(resource_project, monkeypatch):
    """A broken skill stays within the public resource failure contract."""
    docroot = resource_project.resolve_document_path("")
    skill = docroot / "_skills/broken/SKILL.md.mustache"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: broken\ndescription: Broken fixture.\nusage: Use for a rendering failure.\n---\nBroken."
    )

    async def raise_render_error(*args, **kwargs):
        raise RuntimeError("fixture rendering failure")

    monkeypatch.setattr(rendering, "render_template", raise_render_error)

    result = await internal_read_resource(ReadResourceArgs(uri="guide://$broken"), resource_project)

    assert result.success is False
    assert result.error_type == "validation_error"


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
async def test_skill_catalogue_skips_invalid_or_malformed_packages(resource_project):
    """One invalid package cannot hide independently valid Guide skills."""
    skills_dir = resource_project.resolve_document_path("_skills")
    invalid_identifier = skills_dir / "unsafe?skill"
    invalid_identifier.mkdir(parents=True)
    (invalid_identifier / "SKILL.md.mustache").write_text(
        "---\nname: unsafe-skill\ndescription: Invalid package path.\nusage: Never.\n---\nIgnored.",
        encoding="utf-8",
    )
    invalid_name = skills_dir / "invalid-name"
    invalid_name.mkdir()
    (invalid_name / "SKILL.md.mustache").write_text(
        "---\nname: invalid?name\ndescription: Invalid public name.\nusage: Never.\n---\nIgnored.",
        encoding="utf-8",
    )
    malformed = skills_dir / "malformed"
    malformed.mkdir()
    (malformed / "SKILL.md.mustache").write_text("---\nname: [\n---\nIgnored.", encoding="utf-8")

    result = await internal_read_resource(ReadResourceArgs(uri="guide://$"), resource_project)

    assert result.success, result.error
    assert "workflow-status" in result.value
    assert "unsafe?skill" not in result.value
    assert "invalid?name" not in result.value
    assert "malformed" not in result.value


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
