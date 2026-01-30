"""Tests for workflow content rendering."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_guide.workflow.workflow_content import render_workflow_content


@pytest.mark.asyncio
async def test_render_workflow_content_basic():
    """Test basic workflow template rendering."""
    pattern = "monitoring-setup"
    workflow_dir = Path("/test/templates/_workflow")
    context = {"project": "test-project"}
    docroot = Path("/test")

    with (
        patch("mcp_guide.workflow.workflow_content.discover_category_files") as mock_discover,
        patch("mcp_guide.workflow.workflow_content.render_template") as mock_render,
    ):
        # Setup mocks
        file_info = MagicMock()
        file_info.path = workflow_dir / "monitoring-setup.mustache"
        mock_discover.return_value = [file_info]

        rendered_content = MagicMock()
        rendered_content.content = "Rendered workflow content"
        mock_render.return_value = rendered_content

        # Execute
        result = await render_workflow_content(
            pattern=pattern,
            workflow_dir=workflow_dir,
            context=context,
            docroot=docroot,
        )

        # Verify
        assert result == "Rendered workflow content"
        mock_discover.assert_called_once_with(workflow_dir, [pattern])
        mock_render.assert_called_once_with(
            file_info=file_info,
            base_dir=file_info.path.parent,
            project_flags={},
            context=context,
            docroot=docroot,
        )


@pytest.mark.asyncio
async def test_render_workflow_content_no_match():
    """Test error when no template matches pattern."""
    pattern = "nonexistent"
    workflow_dir = Path("/test/templates/_workflow")
    context = {}
    docroot = Path("/test")

    with patch("mcp_guide.workflow.workflow_content.discover_category_files") as mock_discover:
        mock_discover.return_value = []

        with pytest.raises(FileNotFoundError, match="No template found matching pattern"):
            await render_workflow_content(
                pattern=pattern,
                workflow_dir=workflow_dir,
                context=context,
                docroot=docroot,
            )


@pytest.mark.asyncio
async def test_render_workflow_content_multiple_matches():
    """Test error when multiple templates match pattern."""
    pattern = "monitoring-*"
    workflow_dir = Path("/test/templates/_workflow")
    context = {}
    docroot = Path("/test")

    with patch("mcp_guide.workflow.workflow_content.discover_category_files") as mock_discover:
        file1 = MagicMock()
        file1.path = workflow_dir / "monitoring-setup.mustache"
        file2 = MagicMock()
        file2.path = workflow_dir / "monitoring-reminder.mustache"
        mock_discover.return_value = [file1, file2]

        with pytest.raises(FileNotFoundError, match="Multiple templates found"):
            await render_workflow_content(
                pattern=pattern,
                workflow_dir=workflow_dir,
                context=context,
                docroot=docroot,
            )


@pytest.mark.asyncio
async def test_render_workflow_content_render_error():
    """Test handling of template rendering errors."""
    pattern = "monitoring-setup"
    workflow_dir = Path("/test/templates/_workflow")
    context = {}
    docroot = Path("/test")

    with (
        patch("mcp_guide.workflow.workflow_content.discover_category_files") as mock_discover,
        patch("mcp_guide.workflow.workflow_content.render_template") as mock_render,
    ):
        file_info = MagicMock()
        file_info.path = workflow_dir / "monitoring-setup.mustache"
        mock_discover.return_value = [file_info]

        mock_render.side_effect = RuntimeError("Template syntax error")

        # Should return None and log error
        result = await render_workflow_content(
            pattern=pattern,
            workflow_dir=workflow_dir,
            context=context,
            docroot=docroot,
        )

        assert result is None


@pytest.mark.asyncio
async def test_render_workflow_content_permission_error():
    """Test handling of permission errors."""
    pattern = "monitoring-setup"
    workflow_dir = Path("/test/templates/_workflow")
    context = {}
    docroot = Path("/test")

    with (
        patch("mcp_guide.workflow.workflow_content.discover_category_files") as mock_discover,
        patch("mcp_guide.workflow.workflow_content.render_template") as mock_render,
    ):
        file_info = MagicMock()
        file_info.path = workflow_dir / "monitoring-setup.mustache"
        mock_discover.return_value = [file_info]

        mock_render.side_effect = PermissionError("Cannot read file")

        # Should return None and log warning
        result = await render_workflow_content(
            pattern=pattern,
            workflow_dir=workflow_dir,
            context=context,
            docroot=docroot,
        )

        assert result is None


@pytest.mark.asyncio
async def test_render_workflow_content_unicode_error():
    """Test handling of unicode decode errors."""
    pattern = "monitoring-setup"
    workflow_dir = Path("/test/templates/_workflow")
    context = {}
    docroot = Path("/test")

    with (
        patch("mcp_guide.workflow.workflow_content.discover_category_files") as mock_discover,
        patch("mcp_guide.workflow.workflow_content.render_template") as mock_render,
    ):
        file_info = MagicMock()
        file_info.path = workflow_dir / "monitoring-setup.mustache"
        mock_discover.return_value = [file_info]

        mock_render.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid utf-8")

        # Should return None and log error
        result = await render_workflow_content(
            pattern=pattern,
            workflow_dir=workflow_dir,
            context=context,
            docroot=docroot,
        )

        assert result is None


@pytest.mark.asyncio
async def test_render_workflow_content_filtered_by_requires():
    """Test handling when template is filtered by requires-* directives."""
    pattern = "monitoring-setup"
    workflow_dir = Path("/test/templates/_workflow")
    context = {}
    docroot = Path("/test")

    with (
        patch("mcp_guide.workflow.workflow_content.discover_category_files") as mock_discover,
        patch("mcp_guide.workflow.workflow_content.render_template") as mock_render,
    ):
        file_info = MagicMock()
        file_info.path = workflow_dir / "monitoring-setup.mustache"
        mock_discover.return_value = [file_info]

        # render_template returns None when filtered by requires-*
        mock_render.return_value = None

        # Should return None and log debug message
        result = await render_workflow_content(
            pattern=pattern,
            workflow_dir=workflow_dir,
            context=context,
            docroot=docroot,
        )

        assert result is None
