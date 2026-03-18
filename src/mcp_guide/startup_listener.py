"""Startup instruction listener for automatic content injection."""

import asyncio
from typing import TYPE_CHECKING

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.render.rendering import render_content
from mcp_guide.task_manager import get_task_manager

if TYPE_CHECKING:
    from mcp_guide.session import Session

logger = get_logger(__name__)


class StartupInstructionListener:
    """Listener that renders and queues startup instructions. One instance per session."""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()

    def on_config_changed(self, session: "Session") -> None:
        """No-op — startup instructions don't re-fire on config changes."""
        pass

    def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Render and queue startup instructions when a project is loaded."""
        task = asyncio.create_task(self._render_and_queue(session))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _render_and_queue(self, session: "Session") -> None:
        """Render startup template and queue instruction if content is non-blank.

        Args:
            session: The session to render startup instruction for
        """
        try:
            # Use standard render_content to discover and render _startup template
            # render_content handles requires-* filtering automatically
            rendered = await render_content(
                pattern="_startup",
                category_dir="_system",  # Templates are in _system directory
            )

            if rendered and rendered.content.strip():
                task_manager = get_task_manager()
                await task_manager.queue_instruction(rendered.content, priority=True)
                logger.trace(f"Startup instruction queued for project: {session.project_name}")

        except FileNotFoundError as e:
            logger.trace(f"No startup template found for project {session.project_name}: {e}")
        except Exception as e:
            logger.error(f"Error rendering startup instruction for {session.project_name}: {e}", exc_info=True)
