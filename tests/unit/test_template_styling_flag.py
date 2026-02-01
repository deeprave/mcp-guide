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

    async def test_template_styling_invalid_value_defaults_plain(self, template_cache):
        """Test invalid content-style value defaults to plain."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_session = Mock()

            mock_project_flags_obj = Mock()
            mock_project_flags_obj.list = AsyncMock(return_value={FLAG_CONTENT_STYLE: "invalid"})
            mock_session.project_flags.return_value = mock_project_flags_obj

            mock_feature_flags_obj = Mock()
            mock_feature_flags_obj.list = AsyncMock(return_value={})
            mock_session.feature_flags.return_value = mock_feature_flags_obj

            mock_get_session.return_value = mock_session

            context = await template_cache._build_agent_context()

            # Should default to plain when invalid value provided
            assert context["b"] == ""
            assert context["i"] == ""
            assert context["h1"] == ""
            assert context["h2"] == ""
            assert context["h3"] == ""
            assert context["h4"] == ""
            assert context["h5"] == ""
            assert context["h6"] == ""

    async def test_template_styling_session_error_defaults_plain(self, template_cache):
        """Test session access error defaults to plain."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Session error")

            context = await template_cache._build_agent_context()

            # Should default to plain when session access fails
            assert context["b"] == ""
            assert context["i"] == ""
            assert context["h1"] == ""
            assert context["h2"] == ""
            assert context["h3"] == ""
            assert context["h4"] == ""
            assert context["h5"] == ""
            assert context["h6"] == ""

    async def test_template_styling_connection_error_defaults_plain(self, template_cache):
        """Test connection error defaults to plain."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_get_session.side_effect = ConnectionError("Connection failed")

            context = await template_cache._build_agent_context()

            # Should default to plain when connection fails
            assert context["b"] == ""
            assert context["i"] == ""

    async def test_template_styling_flag_resolution_error_defaults_plain(self, template_cache):
        """Test flag resolution error defaults to plain."""
        with patch("mcp_guide.session.get_current_session") as mock_get_session:
            mock_session = Mock()
            mock_project_flags_obj = Mock()
            mock_project_flags_obj.list = AsyncMock(side_effect=KeyError("Flag not found"))
            mock_session.project_flags.return_value = mock_project_flags_obj

            mock_get_session.return_value = mock_session

            context = await template_cache._build_agent_context()

            # Should default to plain when flag resolution fails
            assert context["b"] == ""
            assert context["i"] == ""
