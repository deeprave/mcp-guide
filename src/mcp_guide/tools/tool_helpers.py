"""Shared helpers for tool implementations."""

from typing import TYPE_CHECKING, Optional

from mcp_guide.session import get_session

if TYPE_CHECKING:
    from fastmcp import Context

    from mcp_guide.models.project import Project
    from mcp_guide.session import Session


async def get_session_and_project(ctx: Optional["Context"] = None) -> tuple["Session", Optional["Project"]]:
    """Get session and project, returning None for project if unavailable."""
    session = await get_session(ctx)
    try:
        return session, await session.get_project()
    except ValueError:
        return session, None
