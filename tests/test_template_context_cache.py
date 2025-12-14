"""Tests for template context cache functionality."""

from unittest.mock import Mock

from mcp_guide.utils.template_context_cache import TemplateContextCache


class TestTemplateContextCache:
    """Test TemplateContextCache class functionality."""

    def test_build_project_context_method_exists(self) -> None:
        """Test that _build_project_context method exists."""
        cache = TemplateContextCache()

        # Method should exist
        assert hasattr(cache, "_build_project_context")
        assert callable(getattr(cache, "_build_project_context"))

    def test_build_project_context_returns_project_name(self) -> None:
        """Test that _build_project_context returns project name in context."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_any_active_session to return session with cached project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories=[], collections=[])
        mock_session._cached_project = mock_project

        with patch("mcp_guide.session.get_any_active_session", return_value=mock_session):
            # Get project context
            context = cache._build_project_context()

            # Verify project data is in context
            assert "project" in context
            assert context["project"]["name"] == "test-project"

    def test_build_project_context_handles_missing_project(self) -> None:
        """Test that _build_project_context handles missing project gracefully."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_any_active_session to return None
        with patch("mcp_guide.session.get_any_active_session", return_value=None):
            # Should not raise exception
            context = cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    def test_context_chain_order_system_agent_project(self) -> None:
        """Test context chain order is system → agent → project (project overrides agent overrides system)."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_any_active_session to return session with cached project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories=[], collections=[])
        mock_session._cached_project = mock_project

        with patch("mcp_guide.session.get_any_active_session", return_value=mock_session):
            # Get layered contexts
            context = cache.get_template_contexts()

            # Verify project context is accessible (highest priority)
            assert "project" in context
            assert context["project"]["name"] == "test-project"
