"""Tests for make_no_project_result factory and _check_project_bound."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestProjectRootTemplate:
    """Verify the _project-root.mustache file contains expected instructions."""

    def test_template_contains_git_worktree_detection(self):
        """Template file must instruct the agent to run git rev-parse --git-common-dir."""
        import mcp_guide

        template_path = Path(mcp_guide.__file__).parent / "templates" / "_system" / "_project-root.mustache"
        assert template_path.exists(), f"Template not found: {template_path}"
        content = template_path.read_text()
        assert "git rev-parse --git-common-dir" in content

    def test_template_contains_cwd_fallback(self):
        """Template file must mention a CWD fallback for non-git projects."""
        import mcp_guide

        template_path = Path(mcp_guide.__file__).parent / "templates" / "_system" / "_project-root.mustache"
        content = template_path.read_text()
        # "fall back" or "fallback" — either wording is acceptable
        assert ("fall" in content.lower() and "cwd" in content.lower()) or "working directory" in content.lower()

    def test_template_contains_set_project_instruction(self):
        """Template file must instruct the agent to call set_project."""
        import mcp_guide

        template_path = Path(mcp_guide.__file__).parent / "templates" / "_system" / "_project-root.mustache"
        content = template_path.read_text()
        assert "set_project" in content

    def test_template_has_correct_frontmatter_type(self):
        """Template frontmatter type must be agent/instruction."""
        import mcp_guide

        template_path = Path(mcp_guide.__file__).parent / "templates" / "_system" / "_project-root.mustache"
        content = template_path.read_text()
        assert "type: agent/instruction" in content


class TestMakeNoProjectResult:
    """Tests for the make_no_project_result async factory."""

    @pytest.mark.anyio
    async def test_no_ctx_no_session_returns_static_fallback(self):
        """ctx=None with no active session returns static RESULT_NO_PROJECT."""
        from mcp_guide.result_constants import RESULT_NO_PROJECT, make_no_project_result

        with patch("mcp_guide.session.get_session", new=AsyncMock(side_effect=ValueError("no session"))):
            result = await make_no_project_result(ctx=None)

        assert result is RESULT_NO_PROJECT

    @pytest.mark.anyio
    async def test_no_ctx_session_unexpected_error_logs_and_returns_static_fallback(self, caplog):
        """Unexpected session errors log and return the static RESULT_NO_PROJECT fallback."""
        from mcp_guide.result_constants import RESULT_NO_PROJECT, make_no_project_result

        with (
            caplog.at_level(logging.ERROR, logger="mcp_guide.result_constants"),
            patch("mcp_guide.session.get_session", new=AsyncMock(side_effect=RuntimeError("boom"))),
        ):
            result = await make_no_project_result(ctx=None)

        assert result is RESULT_NO_PROJECT
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        assert any(record.exc_info and "boom" in str(record.exc_info[1]) for record in caplog.records)

    @pytest.mark.anyio
    async def test_render_failure_returns_static_fallback_and_warns(self, caplog):
        """When render_content raises, factory returns static fallback and logs a warning."""
        from mcp_guide.result_constants import RESULT_NO_PROJECT, make_no_project_result

        mock_session = AsyncMock()
        mock_session.project_is_bound = False

        with (
            patch("mcp_guide.session.get_session", new=AsyncMock(return_value=mock_session)),
            patch(
                "mcp_guide.render.rendering.render_content",
                new=AsyncMock(side_effect=RuntimeError("render boom")),
            ),
            caplog.at_level(logging.WARNING, logger="mcp_guide.result_constants"),
        ):
            result = await make_no_project_result(ctx=MagicMock())

        assert result is RESULT_NO_PROJECT
        warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("rendering failed" in m for m in warning_messages)

    @pytest.mark.anyio
    async def test_unbound_session_returns_rendered_result(self):
        """With live session and successful render, factory returns Result with rendered content."""
        from mcp_guide.result_constants import ERROR_NO_PROJECT, RESULT_NO_PROJECT, make_no_project_result

        mock_session = AsyncMock()
        mock_session.project_is_bound = False
        mock_rendered = MagicMock()
        mock_rendered.content = "## Instructions\ngit rev-parse --git-common-dir strips /.git"

        with (
            patch("mcp_guide.session.get_session", new=AsyncMock(return_value=mock_session)),
            patch(
                "mcp_guide.render.rendering.render_content",
                new=AsyncMock(return_value=mock_rendered),
            ),
        ):
            result = await make_no_project_result(ctx=MagicMock())

        assert result is not RESULT_NO_PROJECT
        assert result.error_type == ERROR_NO_PROJECT
        assert "git rev-parse --git-common-dir" in result.instruction

    @pytest.mark.anyio
    async def test_render_returns_none_falls_back_to_static(self):
        """When render_content returns None (filtered), factory returns static fallback."""
        from mcp_guide.result_constants import RESULT_NO_PROJECT, make_no_project_result

        mock_session = AsyncMock()
        mock_session.project_is_bound = False

        with (
            patch("mcp_guide.session.get_session", new=AsyncMock(return_value=mock_session)),
            patch("mcp_guide.render.rendering.render_content", new=AsyncMock(return_value=None)),
        ):
            result = await make_no_project_result(ctx=MagicMock())

        assert result is RESULT_NO_PROJECT

    @pytest.mark.anyio
    async def test_bound_session_returns_static_fallback_without_render(self, caplog):
        """Bound sessions should return the static fallback without rendering the template."""
        from mcp_guide.result_constants import RESULT_NO_PROJECT, make_no_project_result

        mock_session = MagicMock()
        mock_session.project_is_bound = True

        with (
            caplog.at_level(logging.WARNING, logger="mcp_guide.result_constants"),
            patch("mcp_guide.session.get_session", new=AsyncMock(return_value=mock_session)),
            patch("mcp_guide.render.rendering.render_content", new=AsyncMock()) as mock_render,
        ):
            result = await make_no_project_result(ctx=MagicMock())

        assert result is RESULT_NO_PROJECT
        mock_render.assert_not_called()
        assert any("session already bound" in record.getMessage() for record in caplog.records)


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
    async def test_no_session_returns_static_json(self):
        """ValueError from get_session returns static RESULT_NO_PROJECT JSON without calling factory."""
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
            result = await _check_project_bound(ctx=None)

        assert result == RESULT_NO_PROJECT.to_json_str()
        mock_factory.assert_not_called()
