"""Shared helpers for tool implementations."""

from typing import TYPE_CHECKING, Optional

from mcp_guide.models.exceptions import NoProjectError
from mcp_guide.session import get_session

if TYPE_CHECKING:
    from fastmcp import Context

    from mcp_guide.models.project import Project
    from mcp_guide.session import Session


async def get_session_and_project(
    ctx: Optional["Context"] = None, *, session_id: str | None = None
) -> tuple["Session", Optional["Project"]]:
    """Get session and project, returning None for project if unavailable."""
    if session_id is None:
        session = await get_session(ctx)
    else:
        session = await get_session(ctx, session_id=session_id)
    try:
        return session, await session.get_project()
    except NoProjectError:
        return session, None
