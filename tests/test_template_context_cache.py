"""Tests for template context cache functionality."""

from unittest.mock import AsyncMock, Mock

from mcp_guide.utils.template_context_cache import TemplateContextCache


class TestTemplateContextCache:
    """Test TemplateContextCache class functionality."""

    def test_build_project_context_method_exists(self) -> None:
        """Test that _build_project_context method exists."""
        cache = TemplateContextCache()

        # Method should exist
        assert hasattr(cache, "_build_project_context")
        assert callable(getattr(cache, "_build_project_context"))

    async def test_build_project_context_returns_project_name(self) -> None:
        """Test that _build_project_context returns project name in context."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_current_session to return session with project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get project context
            context = await cache._build_project_context()

            # Verify project data is in context
            assert "project" in context
            assert context["project"]["name"] == "test-project"

    async def test_build_project_context_handles_missing_project(self) -> None:
        """Test that _build_project_context handles missing project gracefully."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_or_create_session to return None
        with patch("mcp_guide.session.get_or_create_session", return_value=None):
            # Should not raise exception
            context = await cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    async def test_build_project_context_with_session_without_project_returns_empty_name(self) -> None:
        """Test that _build_project_context handles session without cached project."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_current_session to return session that raises exception on get_project
        mock_session = Mock()
        mock_session.get_project = AsyncMock(side_effect=ValueError("No project"))

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Should not raise exception
            context = await cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    async def test_build_project_context_includes_project_flags(self) -> None:
        """Test that _build_project_context includes project flags in context."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_current_session to return session with project that has flags
        mock_session = Mock()
        mock_project = Project(
            name="test-project",
            categories={},
            collections={},
            project_flags={"phase-tracking": True, "debug-mode": False},
        )
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get project context
            context = await cache._build_project_context()

            # Verify project flags are in context under project.project_flag_values as key-value pairs
            assert "project" in context
            assert "project_flag_values" in context["project"]
            flags_list = context["project"]["project_flag_values"]
            assert isinstance(flags_list, list)

            # Convert back to dict for easier testing
            flags_dict = {item["key"]: item["value"] for item in flags_list}
            assert flags_dict["phase-tracking"] is True
            assert flags_dict["debug-mode"] is False

            # Also verify dict format is available
            assert "project_flags" in context["project"]
            assert context["project"]["project_flags"]["phase-tracking"] is True
            assert context["project"]["project_flags"]["debug-mode"] is False

    async def test_build_project_context_handles_missing_flags(self) -> None:
        """Test that _build_project_context handles projects without flags gracefully."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_current_session to return session with project without flags
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        # No project_flags attribute set
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get project context
            context = await cache._build_project_context()

            # Verify empty flags list and dict are provided
            assert "project" in context
            assert "project_flag_values" in context["project"]
            assert context["project"]["project_flag_values"] == []
            assert "project_flags" in context["project"]
            assert context["project"]["project_flags"] == {}

    async def test_build_project_context_handles_expected_exception(self) -> None:
        """Test that _build_project_context swallows expected exceptions and returns empty project context."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_current_session to raise an expected exception
        with patch(
            "mcp_guide.session.get_current_session",
            side_effect=AttributeError("missing attribute"),
        ):
            # Should not raise exception
            context = await cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    async def test_build_project_context_allows_unexpected_exception_to_propagate(self) -> None:
        """Test that _build_project_context allows unexpected exceptions to propagate naturally."""
        from unittest.mock import patch

        import pytest

        cache = TemplateContextCache()

        # Mock get_current_session to raise a generic unexpected exception
        with patch(
            "mcp_guide.session.get_current_session",
            side_effect=Exception("unexpected error"),
        ):
            # Should propagate the exception naturally
            with pytest.raises(Exception) as exc_info:
                await cache._build_project_context()

            assert "unexpected error" in str(exc_info.value)

    async def test_project_context_accessible_in_layered_contexts(self) -> None:
        """Test that project context is accessible in the layered context chain."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_current_session to return session with project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get layered contexts
            context = await cache.get_template_contexts()

            # Verify project context is accessible (highest priority)
            assert "project" in context
            assert context["project"]["name"] == "test-project"

    async def test_context_precedence_project_overrides_agent_overrides_system(self) -> None:
        """Test that project context values override agent and system values in precedence order."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Clear cache to ensure fresh context
        from mcp_guide.utils.template_context_cache import _template_contexts

        _template_contexts.set(None)

        # Mock get_current_session to return session with project
        mock_session = Mock()
        mock_project = Project(name="project-value", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get layered contexts
            context = await cache.get_template_contexts()

            # Test precedence: project should override server values
            # Server context has "server" key, project should be accessible with higher precedence
            assert "project" in context
            assert context["project"]["name"] == "project-value"

            # Server context should still be accessible
            assert "server" in context
            assert "os" in context["server"]

    async def test_build_category_context_method_exists(self) -> None:
        """Test that _build_category_context method exists."""
        cache = TemplateContextCache()

        # Method should exist
        assert hasattr(cache, "_build_category_context")
        assert callable(getattr(cache, "_build_category_context"))

    async def test_build_category_context_returns_category_data(self) -> None:
        """Test that _build_category_context returns category data in context."""
        from unittest.mock import patch

        from mcp_guide.models import Category, Project

        cache = TemplateContextCache()

        # Mock session with project containing category
        mock_session = Mock()
        test_category = Category(dir="./docs", patterns=["*.md"])
        mock_project = Project(name="test-project", categories={"docs": test_category}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get category context
            context = await cache._build_category_context("docs")

            # Verify category data is in context
            assert "category" in context
            assert context["category"]["name"] == "docs"
            assert context["category"]["dir"] == "./docs"
            assert context["category"]["patterns"][0]["value"] == "*.md"

    async def test_build_category_context_handles_missing_category(self) -> None:
        """Test that _build_category_context handles missing category gracefully."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock session with project without the requested category
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Should not raise exception
            context = await cache._build_category_context("nonexistent")

            # Should return empty category context
            assert "category" in context
            assert context["category"]["name"] == ""

    async def test_complete_context_chain_provides_all_context_types(self) -> None:
        """Test that complete context chain provides access to all context types."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Clear cache to ensure fresh context
        from mcp_guide.utils.template_context_cache import _template_contexts

        _template_contexts.set(None)

        # Mock get_current_session to return session with project
        mock_session = Mock()
        mock_project = Project(name="integration-test", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get complete layered contexts
            context = await cache.get_template_contexts()

            # Verify all context types are accessible
            # Server context
            assert "server" in context
            assert "os" in context["server"]
            assert "platform" in context["server"]
            assert "python_version" in context["server"]

            # Agent context (@ symbol)
            assert "@" in context
            assert context["@"] == "@"

            # Project context
            assert "project" in context
            assert context["project"]["name"] == "integration-test"

    def test_get_transient_context_method_exists(self) -> None:
        """Test that get_transient_context method exists."""
        cache = TemplateContextCache()

        # Method should exist
        assert hasattr(cache, "get_transient_context")
        assert callable(getattr(cache, "get_transient_context"))

    def test_get_transient_context_returns_template_context(self) -> None:
        """Test that get_transient_context returns TemplateContext."""
        from mcp_guide.utils.template_context import TemplateContext

        cache = TemplateContextCache()
        context = cache.get_transient_context()

        assert isinstance(context, TemplateContext)

    def test_get_transient_context_has_required_fields(self) -> None:
        """Test that get_transient_context returns required timestamp fields."""
        cache = TemplateContextCache()
        context = cache.get_transient_context()

        # Test required fields exist
        assert "now" in context
        assert "now_utc" in context
        assert "timestamp" in context
        assert "timestamp_ms" in context
        assert "timestamp_ns" in context

    def test_get_transient_context_field_types(self) -> None:
        """Test that transient context fields have correct types."""
        cache = TemplateContextCache()
        context = cache.get_transient_context()

        # Test field types
        assert isinstance(context["now"], dict)
        assert isinstance(context["now_utc"], dict)
        assert isinstance(context["timestamp"], float)
        assert isinstance(context["timestamp_ms"], float)
        assert isinstance(context["timestamp_ns"], int)

        # Test structured datetime fields
        assert isinstance(context["now"]["date"], str)
        assert isinstance(context["now"]["day"], str)
        assert isinstance(context["now"]["time"], str)
        assert isinstance(context["now"]["tz"], str)
        assert isinstance(context["now"]["datetime"], str)

        assert isinstance(context["now_utc"]["date"], str)
        assert isinstance(context["now_utc"]["day"], str)
        assert isinstance(context["now_utc"]["time"], str)
        assert isinstance(context["now_utc"]["tz"], str)
        assert isinstance(context["now_utc"]["datetime"], str)

    def test_get_transient_context_timezone_awareness(self) -> None:
        """Test that datetime fields contain timezone information."""
        cache = TemplateContextCache()
        context = cache.get_transient_context()

        # Test timezone information is present
        assert context["now"]["tz"]  # Should have timezone offset
        assert context["now_utc"]["tz"] == "+0000"  # UTC always +0000

        # Test datetime strings contain timezone info
        assert context["now"]["datetime"]  # Should have timezone in datetime string
        assert context["now_utc"]["datetime"].endswith("Z")  # UTC should end with Z

    def test_transient_context_freshness(self) -> None:
        """Test that transient context provides fresh timestamps on each call."""
        import time

        cache = TemplateContextCache()

        context1 = cache.get_transient_context()
        time.sleep(0.001)  # Small delay
        context2 = cache.get_transient_context()

        # Timestamps should be different
        assert context1["timestamp_ns"] != context2["timestamp_ns"]
        assert context1["timestamp_ms"] != context2["timestamp_ms"]
        assert context1["timestamp"] != context2["timestamp"]

    def test_transient_context_timestamp_consistency(self) -> None:
        """Test that all timestamp fields represent the same moment."""
        cache = TemplateContextCache()
        context = cache.get_transient_context()

        timestamp_ns = context["timestamp_ns"]
        timestamp_ms = context["timestamp_ms"]
        timestamp = context["timestamp"]

        # Verify calculations are consistent
        expected_timestamp = timestamp_ns / 1_000_000_000
        expected_timestamp_ms = timestamp_ns / 1_000_000

        # Allow small floating point differences
        assert abs(timestamp - expected_timestamp) < 1e-9
        assert abs(timestamp_ms - expected_timestamp_ms) < 1e-6

    async def test_openspec_context_cli_available_project_enabled(self) -> None:
        """Test OpenSpec context with CLI available and project enabled."""
        from unittest.mock import patch

        from mcp_guide.client_context.openspec_task import OpenSpecTask

        cache = TemplateContextCache()

        mock_task = Mock(spec=OpenSpecTask)
        mock_task.is_available.return_value = True
        mock_task.get_version.return_value = "1.2.3"
        mock_task.is_project_enabled.return_value = True

        with patch("mcp_guide.task_manager.get_task_manager") as mock_tm:
            mock_tm.return_value.get_task_by_type.return_value = mock_task
            mock_tm.return_value.get_task_statistics.return_value = {}

            context = await cache._build_agent_context()

            assert context["openspec"]["available"] is True
            assert context["openspec"]["version"] == "1.2.3"
            assert context["openspec"]["enabled"] is True

    async def test_openspec_context_cli_available_project_not_enabled(self) -> None:
        """Test OpenSpec context with CLI available but project not enabled."""
        from unittest.mock import patch

        from mcp_guide.client_context.openspec_task import OpenSpecTask

        cache = TemplateContextCache()

        mock_task = Mock(spec=OpenSpecTask)
        mock_task.is_available.return_value = True
        mock_task.get_version.return_value = "1.2.3"
        mock_task.is_project_enabled.return_value = False

        with patch("mcp_guide.task_manager.get_task_manager") as mock_tm:
            mock_tm.return_value.get_task_by_type.return_value = mock_task
            mock_tm.return_value.get_task_statistics.return_value = {}

            context = await cache._build_agent_context()

            assert context["openspec"]["available"] is True
            assert context["openspec"]["version"] == "1.2.3"
            assert context["openspec"]["enabled"] is False

    async def test_openspec_context_cli_not_available(self) -> None:
        """Test OpenSpec context with CLI not available."""
        from unittest.mock import patch

        from mcp_guide.client_context.openspec_task import OpenSpecTask

        cache = TemplateContextCache()

        mock_task = Mock(spec=OpenSpecTask)
        mock_task.is_available.return_value = False
        mock_task.get_version.return_value = None
        mock_task.is_project_enabled.return_value = None

        with patch("mcp_guide.task_manager.get_task_manager") as mock_tm:
            mock_tm.return_value.get_task_by_type.return_value = mock_task
            mock_tm.return_value.get_task_statistics.return_value = {}

            context = await cache._build_agent_context()

            assert context["openspec"]["available"] is False
            assert context["openspec"]["version"] is None
            assert context["openspec"]["enabled"] is None

    async def test_openspec_context_task_not_registered(self) -> None:
        """Test OpenSpec context when task not registered."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        with patch("mcp_guide.task_manager.get_task_manager") as mock_tm:
            mock_tm.return_value.get_task_by_type.return_value = None
            mock_tm.return_value.get_task_statistics.return_value = {}

            context = await cache._build_agent_context()

            assert context["openspec"]["available"] is False
            assert context["openspec"]["version"] is None
            assert context["openspec"]["enabled"] is False
