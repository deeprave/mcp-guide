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

    @pytest.mark.asyncio
    async def test_read_and_render_with_includes(self):
        """Test content processing with includes in frontmatter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create partial file
            partials_dir = temp_path / "partials"
            partials_dir.mkdir()
            partial_file = partials_dir / "_project.mustache"
            partial_file.write_text("Project: {{project_name}}")

            # Create template with includes
            template_file = temp_path / "status.mustache"
            template_file.write_text("""---
includes: [partials/_project.mustache]
---
# Status
{{>project}}
Current status: active""")

            # Create FileInfo
            file_info = FileInfo(
                path=Path("status.mustache"),
                size=100,
                content_size=80,
                mtime=datetime.now(),
                name="status",
                content=template_file.read_text(),
                frontmatter={"includes": ["partials/_project.mustache"]},
            )

            context = TemplateContext({"project_name": "test-project"})

            errors = await read_and_render_file_contents([file_info], temp_path, context)

            assert len(errors) == 0
            # Should contain rendered partial content
            content = file_info.content
            assert "Project: test-project" in content
            assert "Current status: active" in content

    @pytest.mark.asyncio
    async def test_read_and_render_file_contents_template_error_handling(self):
        """Test that template errors are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create template file with syntax error
            template_file = temp_path / "broken.md.mustache"
            template_file.write_text("Hello {{#unclosed_section}}!")

            files = [
                FileInfo(
                    path=Path("broken.md.mustache"), size=100, content_size=100, mtime=datetime.now(), name="broken.md"
                )
            ]

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

            files = [
                FileInfo(
                    path=Path("test.md.mustache"), size=100, content_size=100, mtime=datetime.now(), name="test.md"
                )
            ]

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
