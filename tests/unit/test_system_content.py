"""Tests for system content rendering utility."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_guide.result import Result
from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.system_content import render_system_content


class TestSystemContent:
    """Test system content rendering functionality."""

    @pytest.mark.asyncio
    async def test_render_system_content_success(self):
        """Should successfully render system content when file exists."""
        from datetime import datetime

        # Mock file discovery
        mock_file_info = FileInfo(
            path=Path("/test/_workflow/monitoring-setup.md.mustache"),
            size=100,
            content_size=80,
            mtime=datetime.now(),
            name="monitoring-setup.md.mustache",
        )

        with (
            patch("mcp_guide.utils.system_content.discover_category_files") as mock_discover,
            patch("mcp_guide.utils.system_content.render_file_content") as mock_render,
        ):
            mock_discover.return_value = [mock_file_info]
            mock_render.return_value = Result.ok("Rendered content")

            result = await render_system_content(
                system_dir=Path("/test/_workflow"),
                pattern="monitoring-setup.*",
                context={"test": "context"},
                docroot=Path("/test"),
            )

            assert result.success
            assert result.value == "Rendered content"
            mock_discover.assert_called_once_with(Path("/test/_workflow"), ["monitoring-setup.*"])
            mock_render.assert_called_once_with(
                mock_file_info, {"test": "context"}, Path("/test/_workflow"), Path("/test")
            )

    @pytest.mark.asyncio
    async def test_render_system_content_no_files_found(self):
        """Should return failure when no files match pattern."""
        with patch("mcp_guide.utils.system_content.discover_category_files") as mock_discover:
            mock_discover.return_value = []

            result = await render_system_content(
                system_dir=Path("/test/_workflow"), pattern="nonexistent.*", context={}, docroot=Path("/test")
            )

            assert not result.success
            assert "No files found matching pattern: nonexistent.*" in result.error

    @pytest.mark.asyncio
    async def test_render_system_content_render_failure(self):
        """Should return failure when file rendering fails."""
        from datetime import datetime

        mock_file_info = FileInfo(
            path=Path("/test/_workflow/monitoring-setup.md.mustache"),
            size=100,
            content_size=80,
            mtime=datetime.now(),
            name="monitoring-setup.md.mustache",
        )

        with (
            patch("mcp_guide.utils.system_content.discover_category_files") as mock_discover,
            patch("mcp_guide.utils.system_content.render_file_content") as mock_render,
        ):
            mock_discover.return_value = [mock_file_info]
            mock_render.return_value = Result.failure("Render error", error_type="render_error")

            result = await render_system_content(
                system_dir=Path("/test/_workflow"), pattern="monitoring-setup.*", context={}, docroot=Path("/test")
            )

            assert not result.success
            assert result.error == "Render error"

    @pytest.mark.asyncio
    async def test_render_system_content_exception_handling(self):
        """Should handle exceptions gracefully."""
        with patch("mcp_guide.utils.system_content.discover_category_files") as mock_discover:
            mock_discover.side_effect = Exception("Discovery failed")

            result = await render_system_content(
                system_dir=Path("/test/_workflow"), pattern="monitoring-setup.*", context={}, docroot=Path("/test")
            )

            assert not result.success
            assert "Error rendering system content: Discovery failed" in result.error
