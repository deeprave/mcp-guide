"""Content batches render real templates and isolate failed files."""

from datetime import datetime

import pytest

from mcp_guide.content.utils import read_and_render_file_contents
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from tests.helpers import create_unbound_test_session, request_context_for


@pytest.fixture
async def content_context(runtime, tmp_path):
    config = runtime.configuration_service().config_file
    config.write_text(f"docroot: {tmp_path}\nprojects: {{}}\n")
    return await request_context_for(create_unbound_test_session(runtime))


def file_info(path):
    stat = path.stat()
    return FileInfo(path, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), path.name)


@pytest.mark.anyio
async def test_batch_renders_templates_and_partials_but_removes_broken_files(content_context, tmp_path):
    partials = tmp_path / "partials"
    partials.mkdir()
    (partials / "_project.mustache").write_text("Project: {{project_name}}\n")
    template = tmp_path / "status.mustache"
    template.write_text("---\nincludes: [partials/project]\n---\n{{>project}}\nStatus: {{status}}")
    regular = tmp_path / "regular.md"
    regular.write_text("# Regular File")
    broken = tmp_path / "broken.mustache"
    broken.write_text("Hello {{#unclosed_section}}!")
    files = [file_info(path) for path in (template, regular, broken)]
    errors = await read_and_render_file_contents(
        content_context, files, tmp_path, TemplateContext({"project_name": "test-project", "status": "active"})
    )
    assert len(errors) == 1
    assert "'broken.mustache' template error" in errors[0]
    assert [item.name for item in files] == ["status.mustache", "regular.md"]
    assert [item.content for item in files] == ["Project: test-project\nStatus: active", "# Regular File"]
    assert [item.content_size for item in files] == [len(item.content.encode("utf-8")) for item in files]


@pytest.mark.anyio
async def test_invalid_template_context_removes_file_with_validation_error(content_context, tmp_path):
    template = tmp_path / "test.mustache"
    template.write_text("Hello {{name}}!")
    files = [file_info(template)]
    errors = await read_and_render_file_contents(content_context, files, tmp_path, {"name": "World"})
    assert errors == ["'test.mustache' template error: Invalid template context type"]
    assert files == []
