"""Tests for template rendering utilities."""

from collections import ChainMap
from datetime import datetime
from pathlib import Path

from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.template_renderer import is_template_file, render_file_content, render_template_content


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
        context = ChainMap({"name": "World"})

        result = render_template_content(content, context)

        assert result.is_ok()
        assert result.value == "Hello World!"

    def test_render_template_content_with_lambda_functions(self):
        """Test template rendering with lambda functions."""
        content = "Created: {{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}"
        context = ChainMap({"created_at": datetime(2023, 12, 25)})

        result = render_template_content(content, context)

        assert result.is_ok()
        assert "2023-12-25" in result.value

    def test_render_template_content_syntax_error(self):
        """Test template rendering with syntax error."""
        content = "Hello {{#unclosed_section}}!"
        context = ChainMap({"name": "World"})

        result = render_template_content(content, context)

        assert result.is_failure()
        assert result.error_type == "template_error"
        assert "Template rendering failed" in result.error

    def test_render_template_content_missing_variable(self):
        """Test template rendering with missing variable."""
        content = "Hello {{missing_var}}!"
        context = ChainMap({"name": "World"})

        result = render_template_content(content, context)

        # Chevron renders missing variables as empty string
        assert result.is_ok()
        assert result.value == "Hello !"


class TestFileContentRendering:
    """Test file content rendering."""

    def test_render_file_content_non_template(self):
        """Test rendering non-template file content."""
        file_info = FileInfo(
            path=Path("test.md"), size=100, mtime=datetime.now(), basename="test.md", content="# Hello World"
        )
        context = ChainMap({"name": "World"})

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
        context = ChainMap({"name": "World"})

        result = render_file_content(file_info, context)

        assert result.is_ok()
        assert result.value == "Hello World!"
        # Check that file size was updated
        assert file_info.size == len("Hello World!")

    def test_render_file_content_no_content_loaded(self):
        """Test rendering file with no content loaded."""
        file_info = FileInfo(path=Path("test.md"), size=100, mtime=datetime.now(), basename="test.md", content=None)
        context = ChainMap({"name": "World"})

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
        context = ChainMap({"name": "World"})

        result = render_file_content(file_info, context)

        assert result.is_failure()
        assert result.error_type == "template_error"
        assert "Template rendering failed" in result.error
