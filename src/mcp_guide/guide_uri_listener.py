"""Guide URI instruction listener for automatic guide:// scheme discovery."""

from typing import TYPE_CHECKING

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.render.rendering import render_content
from mcp_guide.task_manager import get_task_manager

if TYPE_CHECKING:
    from mcp_guide.session import Session

logger = get_logger(__name__)


class GuideUriListener:
    """Listener that renders and queues guide:// URI instructions. One instance per session."""

    async def on_config_changed(self, session: "Session") -> None:
        """No-op — guide URI instructions don't re-fire on config changes."""

    async def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Render and queue guide URI instruction when a project is loaded."""
        await self._render_and_queue(session)

    async def _render_and_queue(self, session: "Session") -> None:
        """Render guide-uri template and queue instruction if content is non-blank."""
        try:
            rendered = await render_content(
                pattern="_guide-uri",
                category_dir="_system",
            )

            if rendered and rendered.content.strip():
                task_manager = get_task_manager()
                await task_manager.queue_instruction(rendered.content)
                logger.trace(f"Guide URI instruction queued for project: {session.project_name}")

        except FileNotFoundError as e:
            logger.trace(f"No guide-uri template found for project {session.project_name}: {e}")
        except Exception as e:
            logger.error(f"Error rendering guide URI instruction for {session.project_name}: {e}", exc_info=True)
