"""Shared test helpers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_guide.session import Session


async def create_bound_test_session(project_name: str, *, _config_dir_for_tests: str) -> "Session":
    """Create a session bound directly to a project for fast test setup."""
    from mcp_guide.session import Session

    session = Session(_config_dir_for_tests=_config_dir_for_tests)
    config_manager = session._get_config_manager(_config_dir_for_tests)
    _key, project = await config_manager.get_or_create_project_config(project_name)
    session._Session__delegate.bind(project)
    session._project_dirty = False
    return session


async def create_test_session(project_name: str, *, _config_dir_for_tests: str) -> "Session":
    """Create a Session using the public project-switch bootstrap path."""
    from mcp_guide.session import Session

    session = Session(_config_dir_for_tests=_config_dir_for_tests)
    await session.switch_project(project_name)
    return session
