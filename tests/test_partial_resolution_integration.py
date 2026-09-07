"""Partial paths are relative to each template, including deeply nested templates."""

from datetime import datetime

import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.template import render_template
from tests.helpers import create_unbound_test_session


@pytest.mark.anyio
@pytest.mark.parametrize(
    "directory,include", [("info", "../_partials/status"), ("workflow/phase", "../../_partials/status")]
)
async def test_partial_resolves_from_template_directory(runtime, tmp_path, directory, include):
    runtime.configuration_service().config_file.write_text("projects: {}\n")
    commands = tmp_path / "commands"
    template_dir = commands / directory
    template_dir.mkdir(parents=True)
    partial_dir = commands / "_partials"
    partial_dir.mkdir()
    (partial_dir / "_status.mustache").write_text("Status: {{status}}")
    template = template_dir / "check.mustache"
    template.write_text(f"---\ntype: user/information\nincludes:\n  - {include}\n---\n{{{{>status}}}}")
    stat = template.stat()
    info = FileInfo(template, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), "check")
    result = await render_template(
        create_unbound_test_session(runtime), info, template_dir, {}, TemplateContext({"status": "checking"})
    )
    assert result is not None
    assert result.content == "Status: checking"
