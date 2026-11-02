"""Tests for template rendering utilities."""

import logging
from datetime import datetime
from pathlib import Path

import anyio
import chevron
import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.functions import TemplateFunctions
from mcp_guide.render.renderer import (
    is_template_file,
    render_template_content,
)
from tests.template_render_cases import TEMPLATE_RENDER_CASES, TemplateRenderCase


class TestTemplateDetection:
    """Test template file detection."""

    @pytest.mark.parametrize(
        "extension,expected",
        [
            (".mustache", True),
            (".hbs", True),
            (".handlebars", True),
            (".chevron", True),
            ("", False),
        ],
    )
    def test_is_template_file(self, extension, expected):
        """Test template detection for various file extensions."""
        file_info = FileInfo(
            path=Path(f"test.md{extension}"), size=100, content_size=100, mtime=datetime.now(), name="test.md"
        )

        assert is_template_file(file_info) is expected


class TestTemplatePartials:
    """Test template rendering with partials."""

    @pytest.mark.anyio
    async def test_render_template_with_partials(self):
        """Test template rendering with partials."""
        content = "{{>project}}"
        context = TemplateContext({"project_name": "test-project"})
        partials = {"project": "Project: {{project_name}}"}

        result = await render_template_content(content, context, partials=partials)

        assert result.is_ok()
        assert result.value is not None
        assert len(result.value.partial_contributions) == 1


class TestTemplateRendering:
    """Test template content rendering."""

    @pytest.mark.anyio
    @pytest.mark.parametrize("case", TEMPLATE_RENDER_CASES, ids=lambda case: case.name)
    async def test_render_case(self, case: TemplateRenderCase):
        """Render each ordinary Guide source-template case through the public boundary."""
        result = await render_template_content(
            case.template,
            case.render_context(),
            file_path=case.file_path,
            partials=dict(case.partials),
        )

        assert result.is_ok()
        assert result.value is not None
        assert result.value.content == case.expected
        assert result.value.errors == []

    @pytest.mark.anyio
    async def test_renderer_does_not_read_implicit_filesystem_partials(self, tmp_path, monkeypatch):
        """Only partials supplied by Guide's guarded loader may be rendered."""
        (tmp_path / "_filesystem_partial.mustache").write_text("untrusted filesystem content")
        monkeypatch.chdir(tmp_path)

        result = await render_template_content("{{>filesystem_partial}}", TemplateContext({}))

        assert result.is_ok()
        assert result.value is not None
        assert result.value.content == ""

    @pytest.mark.anyio
    async def test_chevron_diagnostics_use_guide_logger(self, caplog):
        """Chevron warnings follow Guide's configured rendering logger."""
        caplog.set_level(logging.WARNING, logger="mcp_guide.render.renderer")

        result = await render_template_content("{{missing_value}}", TemplateContext({}))

        assert result.is_ok()
        assert any(
            record.name == "mcp_guide.render.renderer" and "Could not find key 'missing_value'" in record.message
            for record in caplog.records
        )

    @pytest.mark.anyio
    async def test_renderer_rejects_unregistered_callable_context_values(self):
        """Only the explicit Guide lambda registry may execute template callables."""
        calls: list[None] = []

        def unregistered_callable():
            calls.append(None)
            return "must not be rendered"

        result = await render_template_content(
            "{{unregistered}}", TemplateContext({"unregistered": unregistered_callable})
        )

        assert result.is_ok()
        assert result.value is not None
        assert result.value.content == ""
        assert calls == []

    @pytest.mark.anyio
    async def test_renderer_awaits_registered_extensions_concurrently(self, monkeypatch):
        """Independent renders overlap while an extension yields to the active event loop."""
        original = TemplateFunctions.command_args
        active = 0
        maximum_active = 0

        @chevron.compat
        async def observed_command_args(self, text, render=None):
            nonlocal active, maximum_active
            active += 1
            maximum_active = max(maximum_active, active)
            try:
                await anyio.sleep(0)
                return await original(self, text, render)
            finally:
                active -= 1

        monkeypatch.setattr(TemplateFunctions, "command_args", observed_command_args)
        rendered: dict[str, str] = {}

        async def render(label: str, values: str) -> None:
            result = await render_template_content(
                "{{#command-args}}{{values}}{{/command-args}}",
                TemplateContext({"flags": {}, "values": values}),
            )
            assert result.is_ok()
            assert result.value is not None
            rendered[label] = result.value.content

        async with anyio.create_task_group() as task_group:
            task_group.start_soon(render, "first", "one,two")
            task_group.start_soon(render, "second", "three,four")

        assert maximum_active == 2
        assert rendered == {"first": "/one/two", "second": "/three/four"}

    @pytest.mark.anyio
    async def test_render_template_content_syntax_error(self):
        """Test template rendering with syntax error."""
        content = "Hello {{#unclosed_section}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        assert result.is_failure()
        assert result.error_type == "template_error"
        assert result.error is not None
        assert "Template syntax error" in result.error
        assert ">>>    1 |" in result.error  # Check for line context
