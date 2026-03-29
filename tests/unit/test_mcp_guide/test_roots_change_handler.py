"""Tests for roots/list_changed notification handler."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_root(uri: str) -> SimpleNamespace:
    return SimpleNamespace(uri=uri)


def _make_mcp_session(roots: list) -> MagicMock:
    mcp_session = MagicMock()
    result = MagicMock()
    result.roots = roots
    mcp_session.list_roots = AsyncMock(return_value=result)
    return mcp_session


def _make_guide_session(project_name: str, roots: list) -> MagicMock:
    session = MagicMock()
    session.project_name = project_name
    session.project_is_bound = True
    session.roots = roots
    session.try_bind_from_roots = AsyncMock(return_value=True)
    session.template_cache = MagicMock()
    return session


@pytest.mark.anyio
async def test_roots_changed_switches_project() -> None:
    """Roots change to a different project triggers switch_project."""
    from mcp_guide.server import _current_notification_session, _handle_roots_changed

    old_roots = [_make_root("file:///home/user/old-project")]
    new_roots = [_make_root("file:///home/user/new-project")]

    mcp_session = _make_mcp_session(new_roots)
    guide_session = _make_guide_session("old-project", old_roots)

    token = _current_notification_session.set(mcp_session)
    try:
        with patch("mcp_guide.session.get_session_by_mcp_session", return_value=guide_session):
            await _handle_roots_changed(None)
    finally:
        _current_notification_session.reset(token)

    guide_session.try_bind_from_roots.assert_awaited_once_with(new_roots)
    guide_session.template_cache.invalidate.assert_called_once()


@pytest.mark.anyio
async def test_roots_unchanged_is_noop() -> None:
    """Identical roots produce no project switch and no cache invalidation."""
    from mcp_guide.server import _current_notification_session, _handle_roots_changed

    roots = [_make_root("file:///home/user/my-project")]

    mcp_session = _make_mcp_session(roots)
    guide_session = _make_guide_session("my-project", roots)

    token = _current_notification_session.set(mcp_session)
    try:
        with patch("mcp_guide.session.get_session_by_mcp_session", return_value=guide_session):
            await _handle_roots_changed(None)
    finally:
        _current_notification_session.reset(token)

    guide_session.try_bind_from_roots.assert_not_awaited()
    guide_session.template_cache.invalidate.assert_not_called()


def test_create_server_installs_roots_hooks() -> None:
    """create_server patches _handle_message and registers the roots handler."""
    from mcp.types import RootsListChangedNotification

    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import _handle_roots_changed, create_server

    mcp = create_server(ServerConfig())
    low_level = mcp._mcp_server

    assert getattr(low_level._handle_message, "_roots_patched", False), (
        "_handle_message was not patched by create_server"
    )
    assert low_level.notification_handlers.get(RootsListChangedNotification) is _handle_roots_changed, (
        "RootsListChangedNotification handler not registered"
    )
