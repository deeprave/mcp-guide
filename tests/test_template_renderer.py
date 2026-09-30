"""Tests for template rendering utilities."""

from datetime import datetime
from pathlib import Path

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
        assert result.value.content == "Project: test-project"
        assert len(result.value.partial_contributions) == 1

    @pytest.mark.anyio
    async def test_render_template_missing_partial(self):
        """Test template rendering with missing partial."""
        content = "{{>missing}}"
        context = TemplateContext({})
        partials = {}

        result = await render_template_content(content, context, partials=partials)

        # Chevron silently ignores missing partials and renders empty string
        assert result.is_ok()
        assert result.value.content == ""
        assert result.value.partial_contributions == []


class TestTemplateRendering:
    """Test template content rendering."""

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
        rendered_content = result.value.content
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
            rendered_content = result.value.content
            assert rendered_content == expected, f"Expected '{expected}', got '{rendered_content}'"

    @pytest.mark.anyio
    async def test_render_template_content_missing_variable(self):
        """Test template rendering with missing variable."""
        content = "Hello {{missing_var}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        # Chevron renders missing variables as empty string
        assert result.is_ok()
        rendered_content = result.value.content
        assert rendered_content == "Hello !"

    @pytest.mark.anyio
    async def test_help_command_aliases_render_as_uris_by_default(self):
        """Help snippets should use shared command formatting without duplicate punctuation."""
        content = (
            "- `{{#command}}help{{/command}}`{{#aliases_csv}}{{#command-alias}}{{.}}{{/command-alias}}{{/aliases_csv}}"
        )
        context = TemplateContext({"flags": {}, "aliases_csv": "h,project/perm"})

        result = await render_template_content(content, context)

        assert result.is_ok()
        rendered_content = result.value.content
        assert rendered_content == "- `guide://_help` (`guide://_h`, `guide://_project/perm`)"
