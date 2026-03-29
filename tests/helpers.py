"""Shared test helpers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_guide.session import Session


async def create_test_session(project_name: str, *, _config_dir_for_tests: str) -> "Session":
    """Create a bound Session for testing. Replaces Session.create_session."""
    from mcp_guide.session import Session

    session = Session(_config_dir_for_tests=_config_dir_for_tests)
    await session.switch_project(project_name)
    return session
