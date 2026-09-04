"""Shared helpers for tool implementations."""

from typing import TYPE_CHECKING

from mcp_guide.models.exceptions import NoProjectError
from mcp_guide.runtime import RequestContext

if TYPE_CHECKING:
    from mcp_guide.models.project import Project
    from mcp_guide.session import Session


async def get_session_and_project(request_context: RequestContext) -> tuple["Session", "Project | None"]:
    """Return the Session and its current Project, reloading when the Session is stale."""
    session = request_context.session
    if not session.project_is_bound:
        return session, None
    try:
        return session, await session.get_project()
    except NoProjectError:
        return session, None
