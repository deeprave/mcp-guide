"""Tests for GuideUriListener."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.guide_uri_listener import GuideUriListener


class TestGuideUriListener:
    """Test guide URI instruction rendering and queueing."""

    @pytest.mark.anyio
    async def test_on_config_changed_is_noop(self) -> None:
        """on_config_changed should do nothing."""
        listener = GuideUriListener()
        session = MagicMock()
        # Should not raise
        await listener.on_config_changed(session)

    @pytest.mark.anyio
    async def test_queues_instruction_on_project_changed(self) -> None:
        """Should render template and queue instruction without priority."""
        listener = GuideUriListener()
        session = MagicMock()
        session.project_name = "test"

        mock_rendered = MagicMock()
        mock_rendered.content = "guide URI content"
        mock_task_manager = AsyncMock()

        with (
            patch(
                "mcp_guide.guide_uri_listener.render_content", new_callable=AsyncMock, return_value=mock_rendered
            ) as mock_render,
            patch("mcp_guide.guide_uri_listener.get_task_manager", return_value=mock_task_manager),
        ):
            await listener.on_project_changed(session, "old", "new")

            mock_render.assert_awaited_once_with(pattern="_guide-uri", category_dir="_system")
            mock_task_manager.queue_instruction.assert_awaited_once_with(mock_rendered.content)

    @pytest.mark.anyio
    async def test_skips_blank_content(self) -> None:
        """Should not queue instruction when rendered content is blank."""
        listener = GuideUriListener()
        session = MagicMock()
        session.project_name = "test"

        mock_rendered = MagicMock()
        mock_rendered.content = "   "
        mock_task_manager = AsyncMock()

        with (
            patch("mcp_guide.guide_uri_listener.render_content", new_callable=AsyncMock, return_value=mock_rendered),
            patch("mcp_guide.guide_uri_listener.get_task_manager", return_value=mock_task_manager),
        ):
            await listener.on_project_changed(session, "old", "new")

            mock_task_manager.queue_instruction.assert_not_awaited()

    @pytest.mark.anyio
    async def test_handles_template_not_found(self) -> None:
        """Should handle missing template gracefully."""
        listener = GuideUriListener()
        session = MagicMock()
        session.project_name = "test"

        with patch(
            "mcp_guide.guide_uri_listener.render_content",
            new_callable=AsyncMock,
            side_effect=FileNotFoundError("not found"),
        ):
            # Should not raise
            await listener.on_project_changed(session, "old", "new")

    @pytest.mark.anyio
    async def test_handles_render_error(self) -> None:
        """Should handle rendering errors gracefully."""
        listener = GuideUriListener()
        session = MagicMock()
        session.project_name = "test"
        logger_error = MagicMock()

        with (
            patch(
                "mcp_guide.guide_uri_listener.render_content",
                new_callable=AsyncMock,
                side_effect=RuntimeError("render failed"),
            ),
            patch("mcp_guide.guide_uri_listener.logger.error", logger_error),
        ):
            # Should not raise
            await listener.on_project_changed(session, "old", "new")
