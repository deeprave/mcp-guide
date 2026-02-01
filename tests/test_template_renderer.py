"""Tests for template rendering utilities."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.renderer import (
    _build_file_context,
    is_template_file,
    render_template_content,
    render_template_with_context_chain,
)


class TestTemplateDetection:
    """Test template file detection."""

    def test_is_template_file_with_mustache_extension(self):
        """Test template detection for .mustache files."""
        file_info = FileInfo(
            path=Path("test.md.mustache"), size=100, content_size=100, mtime=datetime.now(), name="test.md"
        )

        assert is_template_file(file_info) is True

    def test_is_template_file_with_hbs_extension(self):
        """Test template detection for .hbs files."""


class TestTemplatePartials:
    """Test template rendering with partials."""

    async def test_render_template_with_partials(self):
        """Test template rendering with partials."""
        content = "{{>project}}"
        context = TemplateContext({"project_name": "test-project"})
        partials = {"project": "Project: {{project_name}}"}

        result = await render_template_content(content, context, partials=partials)

        assert result.is_ok()
        assert result.value == "Project: test-project"

    async def test_render_template_missing_partial(self):
        """Test template rendering with missing partial."""
        content = "{{>missing}}"
        context = TemplateContext({})
        partials = {}

        result = await render_template_content(content, context, partials=partials)

        # Chevron silently ignores missing partials and renders empty string
        assert result.is_ok()
        assert result.value == ""


class TestPartialNameExtraction:
    """Test partial name extraction logic."""

    def test_partial_name_extraction_logic(self):
        """Test partial name extraction logic via the public helper."""
        from pathlib import Path

        from mcp_guide.render.renderer import get_partial_name

        # Test cases for partial name extraction
        test_cases = [
            ("_normal.mustache", "normal"),  # Standard case: remove leading underscore
            ("__double.mustache", "_double"),  # Edge case: only remove first underscore
            ("no_underscore.mustache", "no_underscore"),  # No underscore: no change
            ("_", ""),  # Edge case: just underscore
            ("_.mustache", ""),  # Edge case: underscore with extension
            ("path/_partial.mustache", "partial"),  # With directory path
        ]

        for include_path, expected_name in test_cases:
            assert get_partial_name(include_path) == expected_name, (
                f"Failed for {include_path}: expected {expected_name}, got {get_partial_name(include_path)}"
            )
        file_info = FileInfo(path=Path("test.md.hbs"), size=100, content_size=100, mtime=datetime.now(), name="test.md")

        assert is_template_file(file_info) is True

    def test_is_template_file_with_handlebars_extension(self):
        """Test template detection for .handlebars files."""
        file_info = FileInfo(
            path=Path("test.md.handlebars"), size=100, content_size=100, mtime=datetime.now(), name="test.md"
        )

        assert is_template_file(file_info) is True

    def test_is_template_file_with_chevron_extension(self):
        """Test template detection for .chevron files."""
        file_info = FileInfo(
            path=Path("test.md.chevron"), size=100, content_size=100, mtime=datetime.now(), name="test.md"
        )

        assert is_template_file(file_info) is True

    def test_is_template_file_without_mustache_extension(self):
        """Test template detection for non-template files."""
        file_info = FileInfo(path=Path("test.md"), size=100, content_size=100, mtime=datetime.now(), name="test.md")

        assert is_template_file(file_info) is False


class TestTemplateRendering:
    """Test template content rendering."""

    async def test_render_template_content_success(self):
        """Test successful template rendering."""
        content = "Hello {{name}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        assert result.is_ok()
        assert result.value == "Hello World!"

    async def test_render_template_content_with_lambda_functions(self):
        """Test template rendering with lambda functions."""
        content = "Created: {{#format_date}}%Y-%m-%d{{event_date}}{{/format_date}}"
        context = TemplateContext({"event_date": datetime(2023, 12, 25)})

        result = await render_template_content(content, context)

        assert result.is_ok()
        assert "2023-12-25" in result.value

    async def test_render_template_content_syntax_error(self):
        """Test template rendering with syntax error."""
        content = "Hello {{#unclosed_section}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        assert result.is_failure()
        assert result.error_type == "template_error"
        assert "Template syntax error" in result.error
        assert ">>>    1 |" in result.error  # Check for line context

    async def test_template_context_integration_in_pipeline(self):
        """Test that TemplateContext is properly integrated in rendering pipeline."""
        content = "Hello {{name}}! Project: {{project.name}}"
        context = TemplateContext({"name": "World", "project": {"name": "test-project"}})

        result = await render_template_content(content, context)

        assert result.is_ok()
        assert result.value == "Hello World! Project: test-project"

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
            assert result.value == expected, f"Expected '{expected}', got '{result.value}'"

    async def test_render_template_content_missing_variable(self):
        """Test template rendering with missing variable."""
        content = "Hello {{missing_var}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        # Chevron renders missing variables as empty string
        assert result.is_ok()
        assert result.value == "Hello !"

    async def test_render_template_content_accepts_template_context(self):
        """Test that render_template_content accepts TemplateContext."""
        content = "Hello {{name}}!"
        context = TemplateContext({"name": "World"})

        result = await render_template_content(content, context)

        assert result.is_ok()
        assert result.value == "Hello World!"


class TestContextChainRendering:
    """Test context chain wrapper functions."""

    async def test_render_template_with_context_chain_builds_base_context(self) -> None:
        """Test that wrapper builds system → agent → project context chain."""
        content = "Hello {{project.name}}!"

        # Mock the context cache to return a known context
        mock_context = TemplateContext({"project": {"name": "test-project"}})

        with patch("mcp_guide.render.renderer.get_template_contexts", return_value=mock_context):
            result = await render_template_with_context_chain(content)

            assert result.is_ok()
            assert result.value == "Hello test-project!"

    async def test_render_template_with_context_chain_adds_category_context(self) -> None:
        """Test that wrapper adds category context when category_name provided."""
        content = "Category: {{category.name}}"

        # Mock base context (system → agent → project)
        base_context = TemplateContext({"project": {"name": "test-project"}})

        # Mock category context
        category_context = TemplateContext({"category": {"name": "docs"}})

        with patch("mcp_guide.render.renderer.get_template_contexts", return_value=category_context):
            result = await render_template_with_context_chain(content, category_name="docs")

            assert result.is_ok()
            assert result.value == "Category: docs"

    async def test_render_template_with_context_chain_adds_transient_context(self) -> None:
        """Test that wrapper adds transient context with timestamps."""
        content = "Rendered at: {{timestamp}}"

        # Mock base context
        base_context = TemplateContext({"project": {"name": "test-project"}})

        with patch("mcp_guide.render.renderer.get_template_contexts", return_value=base_context):
            result = await render_template_with_context_chain(content)

            assert result.is_ok()
            # Should contain a timestamp (exact value will vary)
            assert "Rendered at:" in result.value
            assert len(result.value) > len("Rendered at: ")


class TestFileContextIsolation:
    """Test per-file context isolation."""

    def test_build_file_context_extracts_file_metadata(self) -> None:
        """Test that _build_file_context extracts file metadata."""
        file_info = FileInfo(
            path=Path("/test/docs/readme.md"),
            size=1024,
            content_size=1024,
            mtime=datetime(2023, 12, 25, 10, 30, 45),
            name="readme",
            content="# Test",
        )

        context = _build_file_context(file_info)

        assert "file" in context
        assert context["file"]["path"] == "/test/docs/readme.md"
        assert context["file"]["name"] == "readme"
        assert context["file"]["size"] == 1024
        assert context["file"]["extension"] == ".md"
        assert context["file"]["is_template"] is False
        assert "2023-12-25" in context["file"]["mtime"]

    def test_build_file_context_detects_template_files(self) -> None:
        """Test that _build_file_context detects template files."""
        file_info = FileInfo(
            path=Path("/test/templates/page.md.mustache"),
            size=512,
            content_size=512,
            mtime=datetime(2023, 12, 25),
            name="page.md",
            content="Hello {{name}}",
        )

        context = _build_file_context(file_info)

        assert context["file"]["is_template"] is True
        assert context["file"]["extension"] == ".mustache"
        assert context["file"]["name"] == "page.md"

    def test_file_context_isolation_using_new_child(self) -> None:
        """Test that file contexts are isolated using new_child()."""
        base_context = TemplateContext({"shared": "value"})

        file1_info = FileInfo(
            path=Path("/test/file1.md"), size=100, content_size=100, mtime=datetime(2023, 12, 25), name="file1"
        )

        file2_info = FileInfo(
            path=Path("/test/file2.md"), size=200, content_size=200, mtime=datetime(2023, 12, 26), name="file2"
        )

        # Build file contexts
        file1_context = _build_file_context(file1_info)
        file2_context = _build_file_context(file2_info)

        # Create isolated contexts
        isolated1 = file1_context.new_child(base_context)
        isolated2 = file2_context.new_child(base_context)

        # Verify isolation
        assert isolated1["file"]["name"] == "file1"
        assert isolated2["file"]["name"] == "file2"
        assert isolated1["shared"] == "value"
        assert isolated2["shared"] == "value"

        # Verify they don't interfere
        assert isolated1["file"]["size"] != isolated2["file"]["size"]

    async def test_render_template_with_context_chain_includes_file_context(self) -> None:
        """Test that wrapper includes file context when FileInfo provided."""
        content = "File: {{file.name}} ({{file.size}} bytes)"

        file_info = FileInfo(
            path=Path("/test/readme.md"), size=1024, content_size=1024, mtime=datetime(2023, 12, 25), name="readme"
        )

        # Mock base context
        base_context = TemplateContext({"project": {"name": "test-project"}})

        with patch("mcp_guide.render.renderer.get_template_contexts", return_value=base_context):
            result = await render_template_with_context_chain(content, file_info=file_info)

            assert result.is_ok()
            assert result.value == "File: readme (1024 bytes)"
