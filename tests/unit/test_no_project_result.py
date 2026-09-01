"""Tests for static no-project results and project-bound checks."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestMakeNoProjectResult:
    """Tests for the make_no_project_result async factory."""

    @pytest.mark.anyio
    async def test_returns_static_result_without_resolving_a_session(self):
        """No-project guidance must not create or inspect request Session state."""
        from mcp_guide.result_constants import RESULT_NO_PROJECT, make_no_project_result

        with patch("mcp_guide.session.get_session", new=AsyncMock()) as get_session:
            result = await make_no_project_result()

        assert result is RESULT_NO_PROJECT
        get_session.assert_not_awaited()


class TestCheckProjectBound:
    """Tests for _check_project_bound behaviour."""

    @pytest.mark.anyio
    async def test_bound_session_returns_none_without_calling_factory(self):
        """Bound session: _check_project_bound returns None and never calls make_no_project_result."""
        from mcp_guide.core.tool_decorator import _check_project_bound

        mock_session = MagicMock()
        mock_session.project_is_bound = True

        with (
            patch(
                "mcp_guide.core.tool_decorator.get_session",
                new=AsyncMock(return_value=mock_session),
            ),
            patch(
                "mcp_guide.core.tool_decorator.make_no_project_result",
                new=AsyncMock(),
            ) as mock_factory,
        ):
            result = await _check_project_bound(ctx=MagicMock())

        assert result is None
        mock_factory.assert_not_called()

    @pytest.mark.anyio
    async def test_no_session_returns_native_static_result(self):
        """ValueError from get_session returns the native static result without rendering."""
        from mcp_guide.core.tool_decorator import _check_project_bound
        from mcp_guide.result_constants import RESULT_NO_PROJECT

        with (
            patch(
                "mcp_guide.core.tool_decorator.get_session",
                new=AsyncMock(side_effect=ValueError("no session")),
            ),
            patch(
                "mcp_guide.core.tool_decorator.make_no_project_result",
                new=AsyncMock(),
            ) as mock_factory,
        ):
            result = await _check_project_bound(ctx=MagicMock())

        assert result.structured_content == RESULT_NO_PROJECT.to_json()
        mock_factory.assert_not_called()

    @pytest.mark.anyio
    async def test_unbound_session_does_not_enter_no_project_rendering(self):
        """The no-project response does not receive a Session."""
        from mcp_guide.core.tool_decorator import _check_project_bound
        from mcp_guide.result import Result

        session = MagicMock()
        session.project_is_bound = False

        with (
            patch("mcp_guide.core.tool_decorator.get_session", new=AsyncMock(return_value=session)),
            patch(
                "mcp_guide.core.tool_decorator.make_no_project_result",
                new=AsyncMock(return_value=Result.failure("No project available")),
            ) as make_result,
        ):
            await _check_project_bound(ctx=MagicMock(), session_id="active-session")

        make_result.assert_awaited_once_with()
