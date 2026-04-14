"""Tests for template rendering utilities."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.renderer import (
    is_template_file,
    render_template_content,
)


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
        rendered_content, partial_frontmatter, _ = result.value
        assert rendered_content == "Project: test-project"
        assert partial_frontmatter == []

    @pytest.mark.anyio
    async def test_render_template_missing_partial(self):
        """Test template rendering with missing partial."""
        content = "{{>missing}}"
        context = TemplateContext({})
        partials = {}

        result = await render_template_content(content, context, partials=partials)

        # Chevron silently ignores missing partials and renders empty string
        assert result.is_ok()
        rendered_content, partial_frontmatter, _ = result.value
        assert rendered_content == ""
        assert partial_frontmatter == []


class TestTemplateRendering:
    """Test template content rendering."""

    @staticmethod
    def _template_body(path: str) -> str:
        content = Path(path).read_text()
        parts = content.split("---\n", 2)
        return parts[2] if len(parts) == 3 else content

    @pytest.mark.anyio
    async def test_render_template_content_success(self):
        """Test successful template rendering."""
        content = "Hello {{name}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert rendered_content == "Hello World!"

    @pytest.mark.anyio
    async def test_render_template_content_with_lambda_functions(self):
        """Test template rendering with lambda functions."""
        content = "Created: {{#format_date}}%Y-%m-%d{{event_date}}{{/format_date}}"
        context = TemplateContext({"event_date": datetime(2023, 12, 25)})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert "2023-12-25" in rendered_content

    @pytest.mark.anyio
    async def test_render_template_content_syntax_error(self):
        """Test template rendering with syntax error."""
        content = "Hello {{#unclosed_section}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        assert result.is_failure()
        assert result.error_type == "template_error"
        assert "Template syntax error" in result.error
        assert ">>>    1 |" in result.error  # Check for line context

    @pytest.mark.anyio
    async def test_template_context_integration_in_pipeline(self):
        """Test that TemplateContext is properly integrated in rendering pipeline."""
        content = "Hello {{name}}! Project: {{project.name}}"
        context = TemplateContext({"name": "World", "project": {"name": "test-project"}})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert rendered_content == "Hello World! Project: test-project"

    @pytest.mark.anyio
    async def test_lambda_functions_injection_in_pipeline(self):
        """Test that lambda functions are properly injected and work in pipeline."""
        from datetime import datetime

        test_cases = [
            (
                "Date: {{#format_date}}%Y-%m-%d{{event_date}}{{/format_date}}",
                {"event_date": datetime(2023, 12, 25)},
                "Date: 2023-12-25",
            ),
            (
                "Text: {{#truncate}}10{{long_text}}{{/truncate}}",
                {"long_text": "This is a very long text that should be truncated"},
                "Text: This is a ...",
            ),  # Fixed expected output
            (
                "Code: {{#highlight_code}}python{{code}}{{/highlight_code}}",
                {"code": "print('hello')"},
                "Code: ```python\nprint('hello')\n```",
            ),
        ]

        for content, context_data, expected in test_cases:
            context = TemplateContext(context_data)
            result = await render_template_content(content, context)

            assert result.is_ok(), f"Failed for: {content}"
            rendered_content, _, _ = result.value
            assert rendered_content == expected, f"Expected '{expected}', got '{rendered_content}'"

    @pytest.mark.anyio
    async def test_render_template_content_missing_variable(self):
        """Test template rendering with missing variable."""
        content = "Hello {{missing_var}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        # Chevron renders missing variables as empty string
        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert rendered_content == "Hello !"

    @pytest.mark.anyio
    async def test_render_template_content_accepts_template_context(self):
        """Test that render_template_content accepts TemplateContext."""
        content = "Hello {{name}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert rendered_content == "Hello World!"

    @pytest.mark.anyio
    async def test_render_template_content_handoff_branch_renders(self):
        """Test that handoff-aware content renders for supported clients."""
        content = """{{#agent.has_handoff}}Separate execution is not available here; continuing inline instead.{{/agent.has_handoff}}"""
        context = TemplateContext({"agent": {"has_handoff": True}})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert rendered_content == "Separate execution is not available here; continuing inline instead."

    @pytest.mark.anyio
    async def test_render_template_content_handoff_branch_omitted_for_fallback_clients(self):
        """Test that handoff-only content is omitted for fallback clients."""
        content = """{{#agent.has_handoff}}Separate execution is not available here; continuing inline instead.{{/agent.has_handoff}}"""
        context = TemplateContext({"agent": {"has_handoff": False}})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert rendered_content == ""

    @pytest.mark.anyio
    async def test_help_command_aliases_render_as_uris_by_default(self):
        """Help snippets should use shared command formatting without duplicate punctuation."""
        content = (
            "- `{{#command}}help{{/command}}`{{#aliases_csv}}{{#command-alias}}{{.}}{{/command-alias}}{{/aliases_csv}}"
        )
        context = TemplateContext({"flags": {}, "aliases_csv": "?,h"})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert rendered_content == "- `guide://_help` (`guide://_?`, `guide://_h`)"

    @pytest.mark.anyio
    async def test_handoff_template_requires_path_and_mode(self):
        """Handoff validation should report missing path and mode distinctly."""
        handoff_template = self._template_body("src/mcp_guide/templates/_commands/handoff.mustache")

        missing_path = await render_template_content(handoff_template, TemplateContext({"args": [], "kwargs": {}}))
        assert missing_path.is_ok()
        _, _, missing_path_errors = missing_path.value
        assert any("Missing required handoff file path" in error for error in missing_path_errors)
        assert not any("exactly one of --read or --write" in error for error in missing_path_errors)

        missing_mode = await render_template_content(
            handoff_template,
            TemplateContext({"args": ["handoff.md"], "kwargs": {}}),
        )
        assert missing_mode.is_ok()
        _, _, missing_mode_errors = missing_mode.value
        assert any("You must specify exactly one of --read or --write." in error for error in missing_mode_errors)
        assert not any("Missing required handoff file path" in error for error in missing_mode_errors)

    @pytest.mark.anyio
    async def test_handoff_template_renders_read_and_write_modes(self):
        """Handoff template should render distinct workflows for read and write modes."""
        handoff_template = self._template_body("src/mcp_guide/templates/_commands/handoff.mustache")

        write_result = await render_template_content(
            handoff_template,
            TemplateContext({"args": ["handoff.md"], "kwargs": {"write": "true"}}),
        )
        assert write_result.is_ok()
        write_rendered, _, write_errors = write_result.value
        assert not write_errors
        assert "Handoff file: `handoff.md`" in write_rendered
        assert "Write your current context and state to the named file." in write_rendered

        with patch.dict("os.environ", {"MCP_PROMPT_NAME": "g"}):
            read_result = await render_template_content(
                handoff_template,
                TemplateContext({"args": ["handoff.md"], "kwargs": {"read": "true"}}),
            )
        assert read_result.is_ok()
        read_rendered, _, read_errors = read_result.value
        assert not read_errors
        assert "Read the named handoff file and use it as input context for the current session." in read_rendered
