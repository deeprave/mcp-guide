"""Startup instruction listener for automatic content injection."""

from typing import TYPE_CHECKING

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.render.rendering import render_content
from mcp_guide.task_manager import get_task_manager

if TYPE_CHECKING:
    from mcp_guide.session import Session

logger = get_logger(__name__)


class StartupInstructionListener:
    """Listener that renders and queues startup instructions. One instance per session."""

    async def on_config_changed(self, session: "Session") -> None:
        """No-op — startup instructions don't re-fire on config changes."""

    async def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Render and queue startup instructions when a project is loaded."""
        await self._render_and_queue(session)

    async def _render_and_queue(self, session: "Session") -> None:
        """Render startup templates and queue instructions if content is non-blank.

        Renders two templates in order:
        - _startup: startup instruction (requires-startup-instruction: true gates it)
        - _onboard_prompt: onboarding notification (requires-onboarded: false gates it)

        Args:
            session: The session to render startup instruction for
        """
        task_manager = get_task_manager()

        try:
            rendered = await render_content(
                pattern="_startup",
                category_dir="_system",
            )
            if rendered and rendered.content.strip():
                await task_manager.queue_instruction(rendered.content, priority=True)
                logger.trace(f"Startup instruction queued for project: {session.project_name}")
        except FileNotFoundError as e:
            logger.trace(f"No startup template found for project {session.project_name}: {e}")
        except Exception as e:
            logger.error(f"Error rendering startup instruction for {session.project_name}: {e}", exc_info=True)

        try:
            rendered = await render_content(
                pattern="_onboard_prompt",
                category_dir="_system",
            )
            if rendered and rendered.content.strip():
                await task_manager.queue_instruction(rendered.content, priority=False)
                logger.trace(f"Onboarding prompt queued for project: {session.project_name}")
        except FileNotFoundError as e:
            logger.trace(f"No onboard prompt template found for project {session.project_name}: {e}")
        except Exception as e:
            logger.error(f"Error rendering onboard prompt for {session.project_name}: {e}", exc_info=True)
