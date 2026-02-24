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
    """Listener that renders and queues startup instructions when sessions are created."""

    def __init__(self) -> None:
        """Initialize the startup instruction listener."""
        self._processed_sessions: set[str] = set()
        self._tasks: set[asyncio.Task[None]] = set()

    def on_session_changed(self, session: "Session") -> None:
        """Handle session change by rendering and queueing startup template.

        Args:
            session: The session that changed
        """
        # Avoid processing the same session multiple times
        if session.project_name in self._processed_sessions:
            return

        self._processed_sessions.add(session.project_name)

        # Create async task and track it
        task = asyncio.create_task(self._render_and_queue(session))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def on_config_changed(self, session: "Session") -> None:
        """Handle config change (no-op for startup instructions).

        Args:
            session: The session whose config changed
        """
        # Startup instructions only trigger on session creation, not config changes
        pass

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
                category_dir="",  # Templates are in docroot
            )

            if rendered and rendered.content.strip():
                task_manager = get_task_manager()
                await task_manager.queue_instruction(rendered.content, priority=True)
                logger.trace(f"Startup instruction queued for project: {session.project_name}")

        except FileNotFoundError as e:
            logger.trace(f"No startup template found for project {session.project_name}: {e}")
        except Exception as e:
            logger.error(f"Error rendering startup instruction for {session.project_name}: {e}", exc_info=True)
