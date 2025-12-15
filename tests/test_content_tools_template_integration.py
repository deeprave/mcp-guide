"""Integration tests for template rendering in content tools."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.utils.content_utils import read_and_render_file_contents
from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.template_context import TemplateContext


class TestContentToolsTemplateIntegration:
    """Test template rendering integration in content tools."""

    @pytest.mark.asyncio
    async def test_read_and_render_file_contents_with_templates(self):
        """Test that read_and_render_file_contents processes templates correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            template_file = temp_path / "test.md.mustache"
            template_file.write_text("Hello {{name}}! Project: {{project.name}}")

            regular_file = temp_path / "regular.md"
            regular_file.write_text("# Regular File")

            # Create FileInfo objects
            files = [
                FileInfo(path=Path("test.md.mustache"), size=100, mtime=datetime.now(), basename="test.md"),
                FileInfo(path=Path("regular.md"), size=50, mtime=datetime.now(), basename="regular"),
            ]

            # Create template context
            context = TemplateContext({"name": "World", "project": {"name": "test-project"}})

            # Process files
            errors = await read_and_render_file_contents(files, temp_path, context)

            # Verify no errors
            assert errors == []

            # Verify template was rendered
            assert files[0].content == "Hello World! Project: test-project"

            # Verify regular file unchanged
            assert files[1].content == "# Regular File"

    @pytest.mark.asyncio
    async def test_read_and_render_file_contents_template_error_handling(self):
        """Test that template errors are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create template file with syntax error
            template_file = temp_path / "broken.md.mustache"
            template_file.write_text("Hello {{#unclosed_section}}!")

            files = [FileInfo(path=Path("broken.md.mustache"), size=100, mtime=datetime.now(), basename="broken.md")]

            context = TemplateContext({"name": "World"})

            # Process files
            errors = await read_and_render_file_contents(files, temp_path, context)

            # Verify template error was captured
            assert len(errors) == 1
            assert "template error" in errors[0]
            assert "broken.md" in errors[0]

            # Verify original content is preserved
            assert files[0].content == "Hello {{#unclosed_section}}!"

    @pytest.mark.asyncio
    async def test_read_and_render_file_contents_invalid_context_validation(self):
        """Test that invalid template context is properly validated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create template file
            template_file = temp_path / "test.md.mustache"
            template_file.write_text("Hello {{name}}!")

            files = [FileInfo(path=Path("test.md.mustache"), size=100, mtime=datetime.now(), basename="test.md")]

            # Pass invalid context (not TemplateContext)
            invalid_context = {"name": "World"}  # Plain dict instead of TemplateContext

            # Process files
            errors = await read_and_render_file_contents(files, temp_path, invalid_context)

            # Verify validation error was captured
            assert len(errors) == 1
            assert "Invalid template context type" in errors[0]
            assert "test.md" in errors[0]

            # Verify original content is preserved
            assert files[0].content == "Hello {{name}}!"
