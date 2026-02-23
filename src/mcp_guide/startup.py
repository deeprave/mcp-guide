"""Startup instruction handling."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_guide.session import Session


async def handle_project_load(session: "Session") -> None:
    """Handle project load - render startup instruction if configured.

    Args:
        session: Session instance with loaded project
    """
    from mcp_guide.discovery.files import FileInfo
    from mcp_guide.render.template import render_template
    from mcp_guide.task_manager import get_task_manager

    # Get project
    project = await session.get_project()

    # Check if startup-instruction flag set
    startup_expr = project.project_flags.get("startup-instruction")
    if not startup_expr:
        return

    # Get docroot from session
    config_manager = session._get_config_manager()
    docroot = await config_manager.get_docroot()

    # Render template (filtering automatic via requires-*)
    file_info = FileInfo(
        path=Path("_startup"),
        category=None,
        size=0,
        content_size=0,
        mtime=datetime.now(),
        name="_startup",
    )

    rendered = await render_template(
        file_info=file_info,
        base_dir=Path(docroot),
        project_flags=project.project_flags,
    )

    if rendered and rendered.content.strip():
        task_manager = get_task_manager()
        await task_manager.queue_instruction(rendered.content, priority=True)
