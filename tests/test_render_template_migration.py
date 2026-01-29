"""Test migration to render_template API."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.render import RenderedContent
from mcp_guide.utils.content_utils import read_and_render_file_contents
from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.frontmatter import Frontmatter
from mcp_guide.utils.template_context import TemplateContext


class TestRenderTemplateAPIIntegration:
    """Test that content_utils uses the render_template API."""

    @pytest.mark.asyncio
    async def test_read_and_render_uses_render_template_api(self):
        """Verify read_and_render_file_contents calls render_template API with correct arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a template file
            template_file = temp_path / "test.md.mustache"
            template_file.write_text("Hello {{name}}!")

            # Create FileInfo with proper initialization
            file_info = FileInfo(
                path=template_file,
                size=len("Hello {{name}}!"),
                content_size=len("Hello {{name}}!"),
                mtime=datetime.now(),
                name="test.md.mustache",
            )

            # Mock render_template to verify it's called
            mock_rendered = RenderedContent(
                frontmatter=Frontmatter({}),
                frontmatter_length=0,
                content="Hello World!",
                content_length=12,
                template_path=template_file,
                template_name="test.md.mustache",
            )

            with patch("mcp_guide.utils.content_utils.render_template", new_callable=AsyncMock) as mock_render:
                mock_render.return_value = mock_rendered

                # Create template context
                context = TemplateContext({"name": "World"})

                # Call read_and_render_file_contents
                files = [file_info]
                errors = await read_and_render_file_contents(
                    files=files, base_dir=temp_path, docroot=temp_path, template_context=context
                )

                # Verify render_template was called exactly once
                mock_render.assert_awaited_once()

                # Verify it was called with the expected arguments
                call_kwargs = mock_render.call_args.kwargs
                assert call_kwargs["file_info"] is file_info
                assert call_kwargs["base_dir"] == temp_path
                assert call_kwargs["docroot"] == temp_path
                assert call_kwargs["context"] is context
                assert "project_flags" in call_kwargs

                # Verify results
                assert len(errors) == 0, "Should have no errors"
                assert len(files) == 1, "Should have one file"
                assert files[0].content == "Hello World!", "Content should be rendered"
