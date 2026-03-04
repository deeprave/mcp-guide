"""Test template styling flag functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.feature_flags.constants import FLAG_CONTENT_STYLE
from mcp_guide.render.cache import TemplateContextCache


class TestTemplateStylingFlag:
    """Test template styling flag behavior."""

    @pytest.fixture
    def template_cache(self):
        """Create a template context cache for testing."""
        cache = TemplateContextCache()
        return cache

    async def test_template_styling_plain_mode(self, template_cache):
        """Test content-style=plain suppresses all formatting."""
        # Mock session methods to return flags
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_session = Mock()

            # Mock project_flags() to return an object with async list() method
            mock_project_flags_obj = Mock()
            mock_project_flags_obj.list = AsyncMock(return_value={FLAG_CONTENT_STYLE: "plain"})
            mock_session.project_flags.return_value = mock_project_flags_obj

            # Mock feature_flags() to return an object with async list() method
            mock_feature_flags_obj = Mock()
            mock_feature_flags_obj.list = AsyncMock(return_value={})
            mock_session.feature_flags.return_value = mock_feature_flags_obj

            mock_get_session.return_value = mock_session

            context = await template_cache._build_agent_context()

            # All formatting should be empty in plain mode
            assert context["b"] == ""
            assert context["i"] == ""
            assert context["h1"] == ""
            assert context["h2"] == ""
            assert context["h3"] == ""
            assert context["h4"] == ""
            assert context["h5"] == ""
            assert context["h6"] == ""

    async def test_template_styling_headings_mode(self, template_cache):
        """Test content-style=headings shows headings but no bold/italic."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_session = Mock()

            mock_project_flags_obj = Mock()
            mock_project_flags_obj.list = AsyncMock(return_value={FLAG_CONTENT_STYLE: "headings"})
            mock_session.project_flags.return_value = mock_project_flags_obj

            mock_feature_flags_obj = Mock()
            mock_feature_flags_obj.list = AsyncMock(return_value={})
            mock_session.feature_flags.return_value = mock_feature_flags_obj

            mock_get_session.return_value = mock_session

            context = await template_cache._build_agent_context()

            # Bold/italic should be empty
            assert context["b"] == ""
            assert context["i"] == ""

            # Headings should be populated
            assert context["h1"] == "# "
            assert context["h2"] == "## "
            assert context["h3"] == "### "
            assert context["h4"] == "#### "
            assert context["h5"] == "##### "
            assert context["h6"] == "###### "

    async def test_template_styling_full_mode(self, template_cache):
        """Test content-style=full enables all formatting."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_session = Mock()

            mock_project_flags_obj = Mock()
            mock_project_flags_obj.list = AsyncMock(return_value={FLAG_CONTENT_STYLE: "full"})
            mock_session.project_flags.return_value = mock_project_flags_obj

            mock_feature_flags_obj = Mock()
            mock_feature_flags_obj.list = AsyncMock(return_value={})
            mock_session.feature_flags.return_value = mock_feature_flags_obj

            mock_get_session.return_value = mock_session

            context = await template_cache._build_agent_context()

            # Bold/italic should be populated
            assert context["b"] == "**"
            assert context["i"] == "*"

            # Headings should be populated
            assert context["h1"] == "# "
            assert context["h2"] == "## "
            assert context["h3"] == "### "
            assert context["h4"] == "#### "
            assert context["h5"] == "##### "
            assert context["h6"] == "###### "

    async def test_template_styling_default_plain(self, template_cache):
        """Test content-style defaults to plain when flag not set."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_session = Mock()

            mock_project_flags_obj = Mock()
            mock_project_flags_obj.list = AsyncMock(return_value={})  # No flag set
            mock_session.project_flags.return_value = mock_project_flags_obj

            mock_feature_flags_obj = Mock()
            mock_feature_flags_obj.list = AsyncMock(return_value={})
            mock_session.feature_flags.return_value = mock_feature_flags_obj

            mock_get_session.return_value = mock_session

            context = await template_cache._build_agent_context()

            # Should default to plain (all empty)
            assert context["b"] == ""
            assert context["i"] == ""
            assert context["h1"] == ""
            assert context["h2"] == ""
            assert context["h3"] == ""
            assert context["h4"] == ""
            assert context["h5"] == ""
            assert context["h6"] == ""

    @pytest.mark.parametrize(
        "error_scenario,mock_setup",
        [
            (
                "invalid_value",
                lambda mock_get_session: _setup_invalid_value_mock(mock_get_session),
            ),
            (
                "session_error",
                lambda mock_get_session: setattr(mock_get_session, "side_effect", Exception("Session error")),
            ),
            (
                "connection_error",
                lambda mock_get_session: setattr(mock_get_session, "side_effect", ConnectionError("Connection failed")),
            ),
            (
                "flag_resolution_error",
                lambda mock_get_session: _setup_flag_resolution_error_mock(mock_get_session),
            ),
        ],
        ids=["invalid_value", "session_error", "connection_error", "flag_resolution_error"],
    )
    async def test_template_styling_error_defaults_plain(self, template_cache, error_scenario, mock_setup):
        """Test various error scenarios default to plain styling."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_setup(mock_get_session)

            context = await template_cache._build_agent_context()

            # Should default to plain when errors occur
            assert context["b"] == ""
            assert context["i"] == ""
            assert context["h1"] == ""
            assert context["h2"] == ""
            assert context["h3"] == ""
            assert context["h4"] == ""
            assert context["h5"] == ""
            assert context["h6"] == ""


def _setup_invalid_value_mock(mock_get_session):
    """Setup mock for invalid value scenario."""
    mock_session = Mock()

    mock_project_flags_obj = Mock()
    mock_project_flags_obj.list = AsyncMock(return_value={FLAG_CONTENT_STYLE: "invalid"})
    mock_session.project_flags.return_value = mock_project_flags_obj

    mock_feature_flags_obj = Mock()
    mock_feature_flags_obj.list = AsyncMock(return_value={})
    mock_session.feature_flags.return_value = mock_feature_flags_obj

    mock_get_session.return_value = mock_session


def _setup_flag_resolution_error_mock(mock_get_session):
    """Setup mock for flag resolution error scenario."""
    mock_session = Mock()
    mock_project_flags_obj = Mock()
    mock_project_flags_obj.list = AsyncMock(side_effect=KeyError("Flag not found"))
    mock_session.project_flags.return_value = mock_project_flags_obj

    mock_get_session.return_value = mock_session
