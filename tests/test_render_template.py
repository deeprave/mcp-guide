"""Tests for render.template module."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.template import render_template as _render_template
from tests.helpers import create_unbound_test_session


@pytest.fixture
def render_template(runtime):
    """Use one explicit Session and minimal configuration for this renderer scenario."""
    runtime.configuration_service().config_file.write_text("projects: {}\n")
    session = create_unbound_test_session(runtime)

    async def render(**kwargs):
        return await _render_template(session=session, **kwargs)

    return render


@pytest.mark.anyio
@pytest.mark.parametrize(
    "scenario,project_flags,expected_result",
    [
        ("flag_present", {"feature": True}, "not_none"),
        ("flag_missing", {}, None),
        ("flag_falsy", {"feature": False}, None),
    ],
)
async def test_render_template_requires_flag(scenario, project_flags, expected_result, render_template, tmp_path):
    """Test render_template with different required flag scenarios."""
    test_file = tmp_path / f"test_requires_{scenario}.mustache"
    test_file.write_text("---\nrequires-feature: true\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags=project_flags,
    )

    if expected_result == "not_none":
        assert result is not None
        assert result.content == "Content"
    else:
        assert result is expected_result


@pytest.mark.anyio
async def test_render_template_requires_list_scalar_match(render_template, tmp_path):
    """Test list requirement with scalar value - should match if in list."""
    test_file = tmp_path / "test_requires_list_scalar.mustache"
    test_file.write_text("---\nrequires-phase: [discussion, planning]\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    # Should match - discussion is in list
    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"phase": "discussion"},
    )
    assert result is not None

    # Should not match - implementation not in list
    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"phase": "implementation"},
    )
    assert result is None


@pytest.mark.anyio
async def test_render_template_requires_list_with_list_any_match(render_template, tmp_path):
    """Test list requirement with list value - should match if ANY required in actual."""
    test_file = tmp_path / "test_requires_list_list.mustache"
    test_file.write_text("---\nrequires-workflow: [discussion, implementation]\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    # Should match - discussion is present
    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"workflow": ["discussion", "planning", "check"]},
    )
    assert result is not None

    # Should not match - neither discussion nor implementation present
    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"workflow": ["planning", "check", "review"]},
    )
    assert result is None


@pytest.mark.anyio
async def test_render_template_requires_workflow_list_matches_boolean_true_default_workflow(render_template, tmp_path):
    """Boolean workflow shorthand should satisfy phase-list requirements via default phases."""
    test_file = tmp_path / "test_requires_workflow_true.mustache"
    test_file.write_text("---\nrequires-workflow: [planning]\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"workflow": True},
    )
    assert result is not None


@pytest.mark.anyio
async def test_render_template_requires_workflow_list_matches_string_true_normalized_workflow(
    render_template, tmp_path
):
    """String workflow booleans should normalize before phase-list matching."""
    test_file = tmp_path / "test_requires_workflow_string_true.mustache"
    test_file.write_text("---\nrequires-workflow: [review]\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"workflow": "true"},
    )
    assert result is not None


@pytest.mark.anyio
async def test_render_template_requires_list_with_dict_any_key(render_template, tmp_path):
    """Test list requirement with dict value - should match if ANY required key exists."""
    test_file = tmp_path / "test_requires_list_dict.mustache"
    test_file.write_text("---\nrequires-config: [feature1, feature2]\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    # Should match - feature1 key exists
    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"config": {"feature1": True, "feature3": False}},
    )
    assert result is not None

    # Should not match - neither feature1 nor feature2 keys exist
    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={"config": {"feature3": True, "feature4": False}},
    )
    assert result is None


@pytest.mark.anyio
async def test_render_template_instruction_with_variable(render_template, tmp_path):
    """Test that template variables in frontmatter instruction field are rendered."""
    test_file = tmp_path / "test_instruction_var.mustache"
    test_file.write_text(
        "---\ninstruction: Follow this policy exactly. If {{workflow.file}} missing, create it.\n---\nContent"
    )

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,  # "Content"
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    # Provide context with workflow.file
    context = TemplateContext({"workflow": {"file": ".guide.yaml"}})

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={},
        context=context,
    )

    assert result is not None
    assert result.template_path == test_file
    assert result.template_name == test_file.name
    assert result.content == "Content"
    # The instruction should have the variable expanded
    # Note: deduplicate_sentences joins sentences with newlines
    assert result.instruction == "Follow this policy exactly.\nIf .guide.yaml missing, create it."


@pytest.mark.anyio
async def test_workflow_phase_template_validates_requested_phase(render_template, tmp_path):
    """The workflow phase command should reject unavailable phases via _error."""
    template_file = Path("src/mcp_guide/templates/_commands/workflow/phase.mustache")
    stat_result = template_file.stat()

    file_info = FileInfo(
        path=template_file,
        size=stat_result.st_size,
        content_size=stat_result.st_size,
        mtime=datetime.fromtimestamp(stat_result.st_mtime),
        name=template_file.name,
    )

    valid_context = TemplateContext(
        {
            "workflow": {
                "file": ".guide.yaml",
                "phase": "discussion",
                "phases": {
                    "discussion": {"next": "planning", "ordered": True},
                    "planning": {"next": "implementation", "ordered": True},
                    "implementation": {"next": "check", "ordered": True},
                    "check": {"next": "review", "ordered": True},
                    "review": {"next": "discussion", "ordered": True},
                    "exploration": {"ordered": False},
                },
                "phase_list": [
                    "discussion",
                    "planning",
                    "implementation",
                    "check",
                    "review",
                    "exploration",
                ],
                "consent": {
                    "discussion": {"any": False},
                    "planning": {"any": False},
                    "implementation": {"any": False},
                    "check": {"any": False},
                    "review": {"any": False},
                    "exploration": {"any": False},
                },
            },
            "args": [{"value": "exploration"}],
            "tool_prefix": "",
        }
    )

    result = await render_template(
        file_info=file_info,
        base_dir=template_file.parent,
        project_flags={"workflow": True},
        context=valid_context,
    )

    assert result is not None
    assert "Requested Phase" in result.content
    assert "`exploration` is available in the configured workflow." in result.content
    assert result.errors == []

    invalid_context = TemplateContext(
        {
            **valid_context.maps[0],
            "args": [{"value": "deploy"}],
        }
    )

    result = await render_template(
        file_info=file_info,
        base_dir=template_file.parent,
        project_flags={"workflow": True},
        context=invalid_context,
    )

    assert result is not None
    assert result.errors == ["Unknown or unavailable workflow phase: deploy"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "template_name",
    [
        "discuss.mustache",
        "explore.mustache",
        "plan.mustache",
        "implement.mustache",
        "check.mustache",
        "review.mustache",
    ],
)
async def test_phase_command_templates_render_general_guidance_without_workflow(
    template_name: str, render_template, tmp_path
):
    """Phase commands should render standalone guidance without workflow state."""
    template_file = Path("src/mcp_guide/templates/_commands/workflow") / template_name
    stat_result = template_file.stat()

    file_info = FileInfo(
        path=template_file,
        size=stat_result.st_size,
        content_size=stat_result.st_size,
        mtime=datetime.fromtimestamp(stat_result.st_mtime),
        name=template_file.name,
    )

    result = await render_template(
        file_info=file_info,
        base_dir=template_file.parent,
        project_flags={"workflow": False},
        context=TemplateContext({"tool_prefix": ""}),
    )

    assert result is not None
    assert "General Guidance" in result.content
    assert ".guide.yaml" not in result.content
    assert "send_file_content" not in result.content
    assert "Guide Workflow Add-in" not in result.content
    if template_name in {"check.mustache", "review.mustache"}:
        assert "Do not modify production code or tests until the user confirms alignment" in result.content


@pytest.mark.anyio
@pytest.mark.parametrize(
    "template_name",
    [
        "discuss.mustache",
        "explore.mustache",
        "plan.mustache",
        "implement.mustache",
        "check.mustache",
        "review.mustache",
    ],
)
async def test_phase_command_templates_append_workflow_guidance_when_enabled(
    template_name: str, render_template, tmp_path
):
    """Workflow context should append, rather than replace, phase guidance."""
    template_file = Path("src/mcp_guide/templates/_commands/workflow") / template_name
    stat_result = template_file.stat()

    file_info = FileInfo(
        path=template_file,
        size=stat_result.st_size,
        content_size=stat_result.st_size,
        mtime=datetime.fromtimestamp(stat_result.st_mtime),
        name=template_file.name,
    )

    result = await render_template(
        file_info=file_info,
        base_dir=template_file.parent,
        project_flags={"workflow": True},
        context=TemplateContext({"workflow": {"file": ".guide.yaml"}, "tool_prefix": ""}),
    )

    assert result is not None
    assert "General Guidance" in result.content
    assert "Guide Workflow Add-in" in result.content


@pytest.mark.anyio
async def test_render_template_description_with_variable(render_template, tmp_path):
    """Test that template variables in frontmatter description field are rendered."""
    test_file = tmp_path / "test_description_var.mustache"
    test_file.write_text("---\ndescription: Project {{project.name}} configuration\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,  # "Content"
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    # Provide context with project.name
    context = TemplateContext({"project": {"name": "mcp-guide"}})

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={},
        context=context,
    )

    assert result is not None
    # The description should have the variable expanded
    assert result.description == "Project mcp-guide configuration"


@pytest.mark.anyio
async def test_render_template_instruction_with_conditional(render_template, tmp_path):
    """Test that conditionals in frontmatter instruction field are rendered."""
    test_file = tmp_path / "test_instruction_conditional.mustache"
    test_file.write_text(
        "---\ninstruction: Follow policy.{{#workflow.consent.exit}} Explicit consent required before {{workflow.next.value}}.{{/workflow.consent.exit}}\n---\nContent"
    )

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,  # "Content"
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    # Provide context with workflow conditional
    context = TemplateContext({"workflow": {"consent": {"exit": True}, "next": {"value": "check"}}})

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={},
        context=context,
    )

    assert result is not None
    # The instruction should have the conditional expanded
    # Note: deduplicate_sentences joins sentences with newlines
    assert result.instruction == "Follow policy.\nExplicit consent required before check."


@pytest.mark.anyio
async def test_render_template_instruction_non_string_ignored(render_template, tmp_path):
    """Test that non-string instruction values are not rendered and don't cause errors."""
    test_file = tmp_path / "test_instruction_non_string.mustache"
    test_file.write_text("---\ninstruction:\n  - item1\n  - item2\n---\nContent")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=7,  # "Content"
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    context = TemplateContext({"project": {"name": "test"}})

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={},
        context=context,
    )

    assert result is not None
    # Non-string instruction should be preserved as-is (list)
    assert isinstance(result.frontmatter.get("instruction"), list)
    assert result.frontmatter["instruction"] == ["item1", "item2"]


@pytest.mark.anyio
async def test_render_template_pre_partials_available_in_template(render_template, tmp_path):
    """pre_partials dict is passed to chevron and available via {{> key}}."""
    test_file = tmp_path / "test_pre_partials.mustache"
    test_file.write_text("---\ntype: agent/instruction\n---\nBefore. {{> git/ops}} After.")

    file_info = FileInfo(
        path=test_file,
        size=test_file.stat().st_size,
        content_size=0,
        mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
        name=test_file.name,
    )

    result = await render_template(
        file_info=file_info,
        base_dir=test_file.parent,
        project_flags={},
        pre_partials={"git/ops": "Policy content here."},
    )

    assert result is not None
    assert "Policy content here." in result.content
    assert "Before." in result.content
    assert "After." in result.content
