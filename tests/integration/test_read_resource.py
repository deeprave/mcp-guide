"""Resource URI routing through real project content and command templates."""

from types import SimpleNamespace

import pytest
from mcp_types import InputRequiredResult

from mcp_guide.models import Category
from mcp_guide.render import rendering
from mcp_guide.render.recommendations import parse_recommendation
from mcp_guide.result_constants import (
    AGENT_ERROR,
    INSTRUCTION_DISPLAY_ONLY,
    USER_INFO,
)
from mcp_guide.tools.tool_resource import (
    ReadResourceArgs,
    internal_read_resource,
    internal_use_skill,
)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "uri,expected",
    [
        ("guide://docs", "docs content"),
        ("guide://docs/readme", "docs content"),
        ("guide://_project", "resource-project verbose"),
        ("guide://_openspec/show/my-change?v", "Show my-change verbose"),
        ("guide://_openspec/show/my-change?verbose=true", "Show my-change verbose"),
        ("guide://_project?table=true", "resource-project verbose table"),
        (
            "guide://$status-snapshot?session_id=resource-session",
            "Read the current status snapshot.",
        ),
    ],
)
async def test_resource_uri_renders_the_bound_projects_content(resource_project, uri, expected):
    result = await internal_read_resource(ReadResourceArgs(uri=uri), resource_project)
    assert result.success, result.error
    assert result.value == expected


@pytest.mark.anyio
async def test_frontmatter_diagnostics_fail_command_and_skill_entrypoints(resource_project):
    """Renderable frontmatter failures must not deliver incomplete instructions."""
    docroot = resource_project.resolve_document_path("")
    (docroot / "_commands/broken.mustache").write_text(
        "---\ninstruction: '{{#_error}}Command configuration is invalid{{/_error}}'\n---\nCommand body"
    )
    skill = docroot / "_skills/broken/SKILL.md.mustache"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\n"
        "name: broken\n"
        "description: '{{#_error}}Skill configuration is invalid{{/_error}}'\n"
        "usage: Use only for this test.\n"
        "---\n"
        "Skill body"
    )

    for uri, field, diagnostic in (
        ("guide://_broken", "instruction", "Command configuration is invalid"),
        ("guide://$broken", "description", "Skill configuration is invalid"),
    ):
        result = await internal_read_resource(ReadResourceArgs(uri=uri), resource_project)
        assert not result.success
        assert result.error_type == "validation_error"
        assert result.disposition == AGENT_ERROR
        assert diagnostic in result.error
        assert result.error_data == {"errors": [f"Frontmatter field '{field}': {diagnostic}"]}


@pytest.mark.anyio
async def test_read_resource_returns_and_resumes_declared_command_input(resource_project):
    """The generic Guide resource route preserves a command interaction."""
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

    pending = await internal_read_resource(
        ReadResourceArgs(uri="guide://_project"), resource_project, mcp_context=context
    )

    assert isinstance(pending, InputRequiredResult)
    accepted = await internal_read_resource(
        ReadResourceArgs(uri="guide://_project"),
        resource_project,
        mcp_context=SimpleNamespace(
            session=context.session,
            request_context=context.request_context,
            request_state=pending.request_state,
            input_responses={"target": SimpleNamespace(action="accept", content={"mode": "branch"})},
        ),
    )

    assert accepted.success, accepted.error
    assert accepted.value == "Project branch"


@pytest.mark.anyio
async def test_use_skill_rejects_member_paths(resource_project):
    result = await internal_use_skill("status-snapshot/README.md", resource_project, kwargs={})

    assert not result.success
    assert result.error_type == "not_found"


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
    skill = docroot / "_skills/guide/git/commit/SKILL.md.mustache"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\n"
        "name: guide-git-commit\n"
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

    result = await internal_read_resource(ReadResourceArgs(uri="guide://$guide-git-commit"), resource_project)

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
async def test_skill_package_member_receives_the_package_context(resource_project):
    """A requested member receives public package URIs and reports its virtual path."""
    result = await internal_read_resource(
        ReadResourceArgs(uri="guide://$status-snapshot/resources/checklist.md?mode=summary"), resource_project
    )

    assert result.success, result.error
    assert result.message == "Rendered skill file: status-snapshot/resources/checklist.md"
    assert result.value == ("Package=status-snapshot; resources=guide://$status-snapshot/resources; mode=summary")


@pytest.mark.anyio
async def test_skill_member_cannot_escape_its_package(resource_project):
    """Traversal cannot read a sibling package or an arbitrary skills-root member."""
    result = await internal_read_resource(
        ReadResourceArgs(uri="guide://$status-snapshot/resources/%2E%2E/%2E%2E/SKILL.md"), resource_project
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
    result = await internal_read_resource(ReadResourceArgs(uri=f"guide://$status-snapshot/{member}"), resource_project)

    assert result.success is False
    assert result.error_type == "validation_error"
    assert result.error == "Guide skill member path must not contain glob syntax"


@pytest.mark.anyio
async def test_missing_skill_member_is_a_structured_not_found_result(resource_project):
    """An unavailable package member does not escape as a renderer exception."""
    result = await internal_read_resource(
        ReadResourceArgs(uri="guide://$status-snapshot/resources/missing.md"), resource_project
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
async def test_table_skill_catalogue_is_user_information_through_read_resource(resource_project):
    """A valueless table query produces a user-facing Markdown table through guide://$."""
    result = await internal_read_resource(ReadResourceArgs(uri="guide://$?table"), resource_project)

    assert result.success, result.error
    assert result.value.startswith("| Skill | Purpose | Use when | Entrypoint |")
    assert "| `status-snapshot` |" in result.value
    assert "| Use when the user asks for a current status snapshot. |" in result.value
    assert "`guide://$status-snapshot`" in result.value
    assert result.disposition == USER_INFO
    assert result.instruction == INSTRUCTION_DISPLAY_ONLY


@pytest.mark.anyio
async def test_skill_requirements_are_filtered_after_shared_discovery(resource_project, runtime):
    """One runtime catalogue is filtered independently for each session's flags."""
    from tests.helpers import create_bound_test_session, request_context_for

    gated = resource_project.resolve_document_path("_skills/gated/SKILL.md.mustache")
    gated.parent.mkdir(parents=True)
    gated.write_text(
        "---\nname: gated\ndescription: A gated skill.\nusage: Use when workflow is enabled.\n"
        "requires-workflow: true\n---\nGated.",
        encoding="utf-8",
    )

    unavailable = await internal_read_resource(ReadResourceArgs(uri="guide://$"), resource_project)
    assert unavailable.success, unavailable.error
    assert "gated" not in unavailable.value
    unavailable_resource = await internal_read_resource(ReadResourceArgs(uri="guide://$gated"), resource_project)
    assert unavailable_resource.success is False
    assert unavailable_resource.error_type == "not_found"

    second_session = await create_bound_test_session(runtime, "gated-second-session")
    await second_session.project_flags().set("workflow", True)
    second_context = await request_context_for(second_session, "gated-second-request")
    available = await internal_read_resource(ReadResourceArgs(uri="guide://$"), second_context)

    assert available.success, available.error
    assert "gated" in available.value
    available_resource = await internal_read_resource(ReadResourceArgs(uri="guide://$gated"), second_context)
    assert available_resource.success, available_resource.error
    assert available_resource.value == "Gated."


@pytest.mark.anyio
async def test_runtime_skill_cache_detects_tree_changes(resource_project, runtime):
    """Skill discovery observes newly added packages on the next request."""
    initial = await internal_read_resource(ReadResourceArgs(uri="guide://$"), resource_project)
    assert initial.success, initial.error
    cached = runtime.skill_discovery_cache
    assert cached is not None
    _, _, cached_skills = cached
    cached_skill = cached_skills["status-snapshot"]
    with pytest.raises(TypeError):
        cached_skill.requirements["requires-workflow"] = True
    refreshed = resource_project.resolve_document_path("_skills/refreshed/SKILL.md.mustache")
    refreshed.parent.mkdir(parents=True)
    refreshed.write_text(
        "---\nname: refreshed\ndescription: A refreshed skill.\nusage: Use to test cache refresh.\n---\nRefreshed.",
        encoding="utf-8",
    )
    after_refresh = await internal_read_resource(ReadResourceArgs(uri="guide://$"), resource_project)
    assert after_refresh.success, after_refresh.error
    assert "refreshed" in after_refresh.value

    development_only = resource_project.resolve_document_path("_skills/refreshed/development/SKILL.md.mustache")
    development_only.parent.mkdir(parents=True)
    development_only.write_text(
        "---\nname: development-only\ndescription: A development-only skill.\n"
        "usage: Use to test development discovery.\n---\nDevelopment.",
        encoding="utf-8",
    )
    after_second_refresh = await internal_read_resource(ReadResourceArgs(uri="guide://$"), resource_project)
    assert after_second_refresh.success, after_second_refresh.error
    assert "development-only" in after_second_refresh.value


@pytest.mark.anyio
async def test_invalid_scheme(resource_project):
    result = await internal_read_resource(ReadResourceArgs(uri="http://example.com"), resource_project)
    assert result.success is False
    assert result.error_type == "validation_error"
    assert "guide://" in result.error


@pytest.mark.anyio
@pytest.mark.slow
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
