"""Test template styling flag functionality."""

from unittest.mock import AsyncMock, Mock

import pytest

from mcp_guide.feature_flags.constants import FLAG_CONTENT_STYLE
from mcp_guide.render.cache import TemplateContextCache


def _session_with_style(*, style: str | None = None, list_side_effect: Exception | None = None) -> Mock:
    """Build a session whose project flags control content-style resolution."""
    mock_session = Mock()
    mock_project_flags_obj = Mock()
    if list_side_effect is not None:
        mock_project_flags_obj.list = AsyncMock(side_effect=list_side_effect)
    elif style is None:
        mock_project_flags_obj.list = AsyncMock(return_value={})
    else:
        mock_project_flags_obj.list = AsyncMock(return_value={FLAG_CONTENT_STYLE: style})
    mock_session.project_flags.return_value = mock_project_flags_obj

    mock_session.agent_info = None
    mock_session.task_manager.get_task_statistics.return_value = {}
    mock_session.task_manager.get_cached_data.return_value = None
    mock_session.get_project = AsyncMock(side_effect=ValueError("no project"))
    return mock_session


@pytest.fixture(autouse=True)
def _runtime_without_global_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = Mock()
    runtime.feature_flags.return_value = Mock(list=AsyncMock(return_value={}))
    monkeypatch.setattr("mcp_guide.runtime.get_runtime", lambda: runtime)


class TestTemplateStylingFlag:
    """Test template styling flag behaviour."""

    @pytest.mark.anyio
    async def test_template_styling_plain_mode(self):
        """Test content-style=plain suppresses all formatting."""
        cache = TemplateContextCache(_session_with_style(style="plain"))

        context = await cache._build_agent_context()

        assert context["b"] == ""
        assert context["i"] == ""
        assert context["h1"] == ""
        assert context["h2"] == ""
        assert context["h3"] == ""
        assert context["h4"] == ""
        assert context["h5"] == ""
        assert context["h6"] == ""

    @pytest.mark.anyio
    async def test_template_styling_headings_mode(self):
        """Test content-style=headings shows headings but no bold/italic."""
        cache = TemplateContextCache(_session_with_style(style="headings"))

        context = await cache._build_agent_context()

        assert context["b"] == ""
        assert context["i"] == ""
        assert context["h1"] == "# "
        assert context["h2"] == "## "
        assert context["h3"] == "### "
        assert context["h4"] == "#### "
        assert context["h5"] == "##### "
        assert context["h6"] == "###### "

    @pytest.mark.anyio
    async def test_template_styling_full_mode(self):
        """Test content-style=full enables all formatting."""
        cache = TemplateContextCache(_session_with_style(style="full"))

        context = await cache._build_agent_context()

        assert context["b"] == "**"
        assert context["i"] == "*"
        assert context["h1"] == "# "
        assert context["h2"] == "## "
        assert context["h3"] == "### "
        assert context["h4"] == "#### "
        assert context["h5"] == "##### "
        assert context["h6"] == "###### "

    @pytest.mark.anyio
    async def test_template_styling_default_plain(self):
        """Test content-style defaults to plain when flag not set."""
        cache = TemplateContextCache(_session_with_style())

        context = await cache._build_agent_context()

        assert context["b"] == ""
        assert context["i"] == ""
        assert context["h1"] == ""
        assert context["h2"] == ""
        assert context["h3"] == ""
        assert context["h4"] == ""
        assert context["h5"] == ""
        assert context["h6"] == ""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "error_cache",
        [
            pytest.param(lambda: TemplateContextCache(_session_with_style(style="invalid")), id="invalid_value"),
            pytest.param(lambda: TemplateContextCache(None), id="session_error"),
            pytest.param(
                lambda: TemplateContextCache(
                    _session_with_style(list_side_effect=ConnectionError("Connection failed"))
                ),
                id="connection_error",
            ),
            pytest.param(
                lambda: TemplateContextCache(_session_with_style(list_side_effect=KeyError("Flag not found"))),
                id="flag_resolution_error",
            ),
        ],
    )
    async def test_template_styling_error_defaults_plain(self, error_cache):
        """Test various error scenarios default to plain styling."""
        context = await error_cache()._build_agent_context()

        assert context["b"] == ""
        assert context["i"] == ""
        assert context["h1"] == ""
        assert context["h2"] == ""
        assert context["h3"] == ""
        assert context["h4"] == ""
        assert context["h5"] == ""
        assert context["h6"] == ""
