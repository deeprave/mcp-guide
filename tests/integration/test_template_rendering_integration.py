"""Flag changes immediately affect conditionals rendered from real project context."""

import pytest

from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.renderer import render_template_content
from mcp_guide.render.rendering import render_content
from tests.helpers import create_bound_test_session


@pytest.mark.anyio
async def test_flag_changes_update_rendered_project_conditionals(runtime):
    runtime.configuration_service().config_file.write_text("projects: {}\n")
    session = await create_bound_test_session(runtime, "render-flags")
    template = "{{#project.project_flags.example}}Enabled{{/project.project_flags.example}}"
    for value, expected in ((True, "Enabled"), (False, ""), (None, "")):
        flags = session.project_flags()
        if value is None:
            await flags.remove("example")
        else:
            await flags.set("example", value)
        context = await get_template_contexts(session)
        result = await render_template_content(template, context)
        assert result.success
        assert result.value is not None
        assert result.value.content == expected
        assert result.value.partial_contributions == []
        assert result.value.errors == []


@pytest.mark.anyio
async def test_render_content_raises_for_frontmatter_diagnostics(runtime, tmp_path):
    docroot = tmp_path / "docs"
    templates = docroot / "templates"
    templates.mkdir(parents=True)
    (templates / "broken.mustache").write_text(
        "---\ndescription: '{{#_error}}Template configuration is invalid{{/_error}}'\n---\nBody"
    )
    runtime.configuration_service().config_file.write_text(f"docroot: {docroot}\nprojects: {{}}\n")
    session = await create_bound_test_session(runtime, "render-diagnostics")

    with pytest.raises(RuntimeError, match="Template configuration is invalid"):
        await render_content(session, "broken", "templates")
