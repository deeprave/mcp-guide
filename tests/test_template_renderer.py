"""Tests for template rendering utilities."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.template_context import TemplateContext
from mcp_guide.utils.template_renderer import (
    _build_file_context,
    is_template_file,
    render_file_content,
    render_template_content,
    render_template_with_context_chain,
)


class TestTemplateDetection:
    """Test template file detection."""

    def test_is_template_file_with_mustache_extension(self):
        """Test template detection for .mustache files."""
        file_info = FileInfo(path=Path("test.md.mustache"), size=100, mtime=datetime.now(), basename="test.md")

        assert is_template_file(file_info) is True

    def test_is_template_file_without_mustache_extension(self):
        """Test template detection for non-template files."""
        file_info = FileInfo(path=Path("test.md"), size=100, mtime=datetime.now(), basename="test.md")

        assert is_template_file(file_info) is False


class TestTemplateRendering:
    """Test template content rendering."""

    def test_render_template_content_success(self):
        """Test successful template rendering."""
        content = "Hello {{name}}!"
        context = TemplateContext({"name": "World"})

        result = render_template_content(content, context)

        assert result.is_ok()
        assert result.value == "Hello World!"

    def test_render_template_content_with_lambda_functions(self):
        """Test template rendering with lambda functions."""
        content = "Created: {{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}"
        context = TemplateContext({"created_at": datetime(2023, 12, 25)})

        result = render_template_content(content, context)

        assert result.is_ok()
        assert "2023-12-25" in result.value

    def test_render_template_content_syntax_error(self):
        """Test template rendering with syntax error."""
        content = "Hello {{#unclosed_section}}!"
        context = TemplateContext({"name": "World"})

        result = render_template_content(content, context)

        assert result.is_failure()
        assert result.error_type == "template_error"
        assert "Template rendering failed" in result.error

    def test_template_context_integration_in_pipeline(self):
        """Test that TemplateContext is properly integrated in rendering pipeline."""
        content = "Hello {{name}}! Project: {{project.name}}"
        context = TemplateContext({"name": "World", "project": {"name": "test-project"}})

        result = render_template_content(content, context)

        assert result.is_ok()
        assert result.value == "Hello World! Project: test-project"

    def test_lambda_functions_injection_in_pipeline(self):
        """Test that lambda functions are properly injected and work in pipeline."""
        from datetime import datetime

        test_cases = [
            (
                "Date: {{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}",
                {"created_at": datetime(2023, 12, 25)},
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
            result = render_template_content(content, context)

            assert result.is_ok(), f"Failed for: {content}"
            assert result.value == expected, f"Expected '{expected}', got '{result.value}'"

    def test_render_template_content_missing_variable(self):
        """Test template rendering with missing variable."""
        content = "Hello {{missing_var}}!"
        context = TemplateContext({"name": "World"})

        result = render_template_content(content, context)

        # Chevron renders missing variables as empty string
        assert result.is_ok()
        assert result.value == "Hello !"

    def test_render_template_content_accepts_template_context(self):
        """Test that render_template_content accepts TemplateContext."""
        content = "Hello {{name}}!"
        context = TemplateContext({"name": "World"})

        result = render_template_content(content, context)

        assert result.is_ok()
        assert result.value == "Hello World!"


class TestFileContentRendering:
    """Test file content rendering."""

    def test_render_file_content_non_template(self):
        """Test rendering non-template file content."""
        file_info = FileInfo(
            path=Path("test.md"), size=100, mtime=datetime.now(), basename="test.md", content="# Hello World"
        )
        context = TemplateContext({"name": "World"})

        result = render_file_content(file_info, context)

        assert result.is_ok()
        assert result.value == "# Hello World"

    def test_render_file_content_template_without_context(self):
        """Test rendering template file without context."""
        file_info = FileInfo(
            path=Path("test.md.mustache"), size=100, mtime=datetime.now(), basename="test.md", content="Hello {{name}}!"
        )

        result = render_file_content(file_info, None)

        assert result.is_ok()
        assert result.value == "Hello {{name}}!"

    def test_render_file_content_template_with_context(self):
        """Test rendering template file with context."""
        file_info = FileInfo(
            path=Path("test.md.mustache"), size=100, mtime=datetime.now(), basename="test.md", content="Hello {{name}}!"
        )
        context = TemplateContext({"name": "World"})

        result = render_file_content(file_info, context)

        assert result.is_ok()
        assert result.value == "Hello World!"
        # Check that file size was updated
        assert file_info.size == len("Hello World!")

    def test_render_file_content_accepts_template_context(self):
        """Test that render_file_content accepts TemplateContext."""
        file_info = FileInfo(
            path=Path("test.md.mustache"), size=100, mtime=datetime.now(), basename="test.md", content="Hello {{name}}!"
        )
        context = TemplateContext({"name": "World"})

        result = render_file_content(file_info, context)

        assert result.is_ok()
        assert result.value == "Hello World!"

    def test_render_file_content_no_content_loaded(self):
        """Test rendering file with no content loaded."""
        file_info = FileInfo(path=Path("test.md"), size=100, mtime=datetime.now(), basename="test.md", content=None)
        context = TemplateContext({"name": "World"})

        result = render_file_content(file_info, context)

        assert result.is_failure()
        assert result.error_type == "content_error"
        assert "File content not loaded" in result.error

    def test_render_file_content_template_error(self):
        """Test rendering template file with syntax error."""
        file_info = FileInfo(
            path=Path("test.md.mustache"),
            size=100,
            mtime=datetime.now(),
            basename="test.md",
            content="Hello {{#unclosed}}!",
        )
        context = TemplateContext({"name": "World"})

        result = render_file_content(file_info, context)

        assert result.is_failure()
        assert result.error_type == "template_error"
        assert "Template rendering failed" in result.error


class TestContextChainRendering:
    """Test context chain wrapper functions."""

    async def test_render_template_with_context_chain_builds_base_context(self) -> None:
        """Test that wrapper builds system → agent → project context chain."""
        content = "Hello {{project.name}}!"

        # Mock the context cache to return a known context
        mock_context = TemplateContext({"project": {"name": "test-project"}})

        with patch("mcp_guide.utils.template_renderer.get_template_contexts", return_value=mock_context):
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

        with patch("mcp_guide.utils.template_renderer.get_template_contexts", return_value=category_context):
            result = await render_template_with_context_chain(content, category_name="docs")

            assert result.is_ok()
            assert result.value == "Category: docs"

    async def test_render_template_with_context_chain_adds_transient_context(self) -> None:
        """Test that wrapper adds transient context with timestamps."""
        content = "Rendered at: {{timestamp}}"

        # Mock base context
        base_context = TemplateContext({"project": {"name": "test-project"}})

        with patch("mcp_guide.utils.template_renderer.get_template_contexts", return_value=base_context):
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
            mtime=datetime(2023, 12, 25, 10, 30, 45),
            basename="readme",
            content="# Test",
        )

        context = _build_file_context(file_info)

        assert "file" in context
        assert context["file"]["path"] == "/test/docs/readme.md"
        assert context["file"]["basename"] == "readme"
        assert context["file"]["size"] == 1024
        assert context["file"]["extension"] == ".md"
        assert context["file"]["is_template"] is False
        assert "2023-12-25" in context["file"]["mtime"]

    def test_build_file_context_detects_template_files(self) -> None:
        """Test that _build_file_context detects template files."""
        file_info = FileInfo(
            path=Path("/test/templates/page.md.mustache"),
            size=512,
            mtime=datetime(2023, 12, 25),
            basename="page.md",
            content="Hello {{name}}",
        )

        context = _build_file_context(file_info)

        assert context["file"]["is_template"] is True
        assert context["file"]["extension"] == ".mustache"
        assert context["file"]["basename"] == "page.md"

    def test_file_context_isolation_using_new_child(self) -> None:
        """Test that file contexts are isolated using new_child()."""
        base_context = TemplateContext({"shared": "value"})

        file1_info = FileInfo(path=Path("/test/file1.md"), size=100, mtime=datetime(2023, 12, 25), basename="file1")

        file2_info = FileInfo(path=Path("/test/file2.md"), size=200, mtime=datetime(2023, 12, 26), basename="file2")

        # Build file contexts
        file1_context = _build_file_context(file1_info)
        file2_context = _build_file_context(file2_info)

        # Create isolated contexts
        isolated1 = file1_context.new_child(base_context)
        isolated2 = file2_context.new_child(base_context)

        # Verify isolation
        assert isolated1["file"]["basename"] == "file1"
        assert isolated2["file"]["basename"] == "file2"
        assert isolated1["shared"] == "value"
        assert isolated2["shared"] == "value"

        # Verify they don't interfere
        assert isolated1["file"]["size"] != isolated2["file"]["size"]

    async def test_render_template_with_context_chain_includes_file_context(self) -> None:
        """Test that wrapper includes file context when FileInfo provided."""
        content = "File: {{file.basename}} ({{file.size}} bytes)"

        file_info = FileInfo(path=Path("/test/readme.md"), size=1024, mtime=datetime(2023, 12, 25), basename="readme")

        # Mock base context
        base_context = TemplateContext({"project": {"name": "test-project"}})

        with patch("mcp_guide.utils.template_renderer.get_template_contexts", return_value=base_context):
            result = await render_template_with_context_chain(content, file_info=file_info)

            assert result.is_ok()
            assert result.value == "File: readme (1024 bytes)"
