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

        # Mock get_current_session to return session with cached project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories=[], collections=[])
        mock_session._cached_project = mock_project

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get project context
            context = cache._build_project_context()

            # Verify project data is in context
            assert "project" in context
            assert context["project"]["name"] == "test-project"

    def test_build_project_context_handles_missing_project(self) -> None:
        """Test that _build_project_context handles missing project gracefully."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_current_session to return None
        with patch("mcp_guide.session.get_current_session", return_value=None):
            # Should not raise exception
            context = cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    def test_build_project_context_with_session_without_project_returns_empty_name(self) -> None:
        """Test that _build_project_context handles session without cached project."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_current_session to return session without cached project
        mock_session = Mock()
        mock_session._cached_project = None

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Should not raise exception
            context = cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    def test_build_project_context_handles_expected_exception(self) -> None:
        """Test that _build_project_context swallows expected exceptions and returns empty project context."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_current_session to raise an expected exception
        with patch(
            "mcp_guide.session.get_current_session",
            side_effect=AttributeError("missing attribute"),
        ):
            # Should not raise exception
            context = cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    def test_build_project_context_propagates_unexpected_exception(self) -> None:
        """Test that _build_project_context propagates unexpected exceptions."""
        from unittest.mock import patch

        import pytest

        cache = TemplateContextCache()

        # Mock get_current_session to raise a generic unexpected exception
        with patch(
            "mcp_guide.session.get_current_session",
            side_effect=Exception("unexpected error"),
        ):
            # Should propagate the exception
            with pytest.raises(Exception) as exc_info:
                cache._build_project_context()

            assert "unexpected error" in str(exc_info.value)

    def test_project_context_accessible_in_layered_contexts(self) -> None:
        """Test that project context is accessible in the layered context chain."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_current_session to return session with cached project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories=[], collections=[])
        mock_session._cached_project = mock_project

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get layered contexts
            context = cache.get_template_contexts()

            # Verify project context is accessible (highest priority)
            assert "project" in context
            assert context["project"]["name"] == "test-project"
