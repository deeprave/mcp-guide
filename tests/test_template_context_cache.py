"""Tests for template context cache functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.render.cache import TemplateContextCache


class TestTemplateContextCache:
    """Test TemplateContextCache class functionality."""

    @pytest.mark.anyio
    async def test_build_project_context_returns_project_name(self) -> None:
        """Test that _build_project_context returns project name in context."""
        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_session to return session with project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_session", return_value=mock_session):
            # Get project context
            context = await cache._build_project_context()

            # Verify project data is in context
            assert "project" in context
            assert context["project"]["name"] == "test-project"

    @pytest.mark.anyio
    async def test_build_project_context_handles_missing_project(self) -> None:
        """Test that _build_project_context handles missing project gracefully."""
        cache = TemplateContextCache()

        # Mock get_session to return None
        with patch("mcp_guide.session.get_session", return_value=None):
            # Should not raise exception
            context = await cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    @pytest.mark.anyio
    async def test_build_project_context_with_session_without_project_returns_empty_name(self) -> None:
        """Test that _build_project_context handles session without cached project."""
        from unittest.mock import patch

        cache = TemplateContextCache()

        # Mock get_session to return session that raises exception on get_project
        mock_session = Mock()
        mock_session.get_project = AsyncMock(side_effect=ValueError("No project"))
        logger_error = Mock()

        with (
            patch("mcp_guide.session.get_session", return_value=mock_session),
            patch("mcp_guide.render.cache.logger.error", logger_error),
        ):
            # Should not raise exception
            context = await cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    @pytest.mark.anyio
    async def test_build_project_context_includes_project_flags(self) -> None:
        """Test that _build_project_context includes project flags in context."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_session to return session with project that has flags
        mock_session = Mock()
        mock_project = Project(
            name="test-project",
            categories={},
            collections={},
            project_flags={"phase-tracking": True, "debug-mode": False},
        )
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_session", return_value=mock_session):
            # Get project context
            context = await cache._build_project_context()

            # Verify project flags are in context under project.project_flag_values as key-value pairs
            assert "project" in context
            assert "project_flag_values" in context["project"]
            flags_list = context["project"]["project_flag_values"]
            assert isinstance(flags_list, list)

            # Convert back to dict for easier testing
            flags_dict = {item["key"]: item["value"] for item in flags_list}
            assert flags_dict["phase-tracking"] == "true"
            assert flags_dict["debug-mode"] == "false"

            # Also verify wrapped dict format is available
            assert "project_flags" in context["project"]
            assert context["project"]["project_flags"]["phase-tracking"] == FeatureValue(True)
            assert context["project"]["project_flags"]["debug-mode"] == FeatureValue(False)

    @pytest.mark.anyio
    async def test_build_project_context_handles_missing_flags(self) -> None:
        """Test that _build_project_context handles projects without flags gracefully."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_session to return session with project without flags
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        # No project_flags attribute set
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_session", return_value=mock_session):
            # Get project context
            context = await cache._build_project_context()

            # Verify empty flags list and dict are provided
            assert "project" in context
            assert "project_flag_values" in context["project"]
            assert context["project"]["project_flag_values"] == []
            assert "project_flags" in context["project"]
            assert context["project"]["project_flags"] == {}

    @pytest.mark.anyio
    async def test_build_project_context_handles_expected_exception(self) -> None:
        """Test that _build_project_context swallows expected exceptions and returns empty project context."""
        from unittest.mock import patch

        cache = TemplateContextCache()
        logger_error = Mock()

        # Mock get_session to raise an expected exception
        with (
            patch(
                "mcp_guide.session.get_session",
                side_effect=AttributeError("missing attribute"),
            ),
            patch("mcp_guide.render.cache.logger.error", logger_error),
        ):
            # Should not raise exception
            context = await cache._build_project_context()

            # Should return empty project context
            assert "project" in context
            assert context["project"]["name"] == ""

    @pytest.mark.anyio
    async def test_build_project_context_allows_unexpected_exception_to_propagate(self) -> None:
        """Test that _build_project_context allows unexpected exceptions to propagate naturally."""
        from unittest.mock import patch

        import pytest

        cache = TemplateContextCache()

        # Mock get_session to raise a generic unexpected exception
        with patch(
            "mcp_guide.session.get_session",
            side_effect=Exception("unexpected error"),
        ):
            # Should propagate the exception naturally
            with pytest.raises(Exception) as exc_info:
                await cache._build_project_context()

            assert "unexpected error" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_project_context_accessible_in_layered_contexts(self) -> None:
        """Test that project context is accessible in the layered context chain."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock get_session to return session with project
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_session", return_value=mock_session):
            # Get layered contexts
            context = await cache.get_template_contexts()

            # Verify project context is accessible (highest priority)
            assert "project" in context
            assert context["project"]["name"] == "test-project"

    @pytest.mark.anyio
    async def test_context_precedence_project_overrides_agent_overrides_system(self) -> None:
        """Test that project context values override agent and system values in precedence order."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Clear cache to ensure fresh context
        from mcp_guide.render.cache import invalidate_template_context_cache

        invalidate_template_context_cache()

        # Mock get_session to return session with project
        mock_session = Mock()
        mock_project = Project(name="project-value", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_session", return_value=mock_session):
            # Get layered contexts
            context = await cache.get_template_contexts()

            # Test precedence: project should override server values
            # Server context has "server" key, project should be accessible with higher precedence
            assert "project" in context
            assert context["project"]["name"] == "project-value"

            # Server context should still be accessible
            assert "server" in context
            assert "os" in context["server"]

    @pytest.mark.anyio
    async def test_build_category_context_method_exists(self) -> None:
        """Test that _build_category_context method exists."""
        cache = TemplateContextCache()

        # Method should exist
        assert hasattr(cache, "_build_category_context")
        assert callable(getattr(cache, "_build_category_context"))

    @pytest.mark.anyio
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

        with patch("mcp_guide.session.get_session", return_value=mock_session):
            # Get category context
            context = await cache._build_category_context("docs")

            # Verify category data is in context
            assert "category" in context
            assert context["category"]["name"] == "docs"
            assert context["category"]["dir"] == "./docs/"
            assert context["category"]["patterns"][0]["value"] == "*.md"

    @pytest.mark.anyio
    async def test_build_category_context_handles_missing_category(self) -> None:
        """Test that _build_category_context handles missing category gracefully."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Mock session with project without the requested category
        mock_session = Mock()
        mock_project = Project(name="test-project", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_session", return_value=mock_session):
            # Should not raise exception
            context = await cache._build_category_context("nonexistent")

            # Should return empty category context
            assert "category" in context
            assert context["category"]["name"] == ""

    @pytest.mark.anyio
    async def test_complete_context_chain_provides_all_context_types(self) -> None:
        """Test that complete context chain provides access to all context types."""
        from unittest.mock import patch

        from mcp_guide.models import Project

        cache = TemplateContextCache()

        # Clear cache to ensure fresh context
        from mcp_guide.render.cache import invalidate_template_context_cache

        invalidate_template_context_cache()

        # Mock get_session to return session with project
        mock_session = Mock()
        mock_session.agent_info = None  # No agent info
        mock_project = Project(name="integration-test", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_session", return_value=mock_session):
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

    def test_get_transient_context_structure(self) -> None:
        """Test that get_transient_context returns correct structure and types."""
        from mcp_guide.render.context import TemplateContext

        cache = TemplateContextCache()

        # Method exists and returns TemplateContext
        assert hasattr(cache, "get_transient_context")
        assert callable(getattr(cache, "get_transient_context"))

        context = cache.get_transient_context()
        assert isinstance(context, TemplateContext)

        # Required fields exist
        required_fields = ["now", "now_utc", "timestamp", "timestamp_ms", "timestamp_ns"]
        for field in required_fields:
            assert field in context

        # Field types are correct
        assert isinstance(context["now"], dict)
        assert isinstance(context["now_utc"], dict)
        assert isinstance(context["timestamp"], float)
        assert isinstance(context["timestamp_ms"], float)
        assert isinstance(context["timestamp_ns"], int)

        # Structured datetime fields
        for dt_field in ["now", "now_utc"]:
            assert isinstance(context[dt_field]["date"], str)
            assert isinstance(context[dt_field]["day"], str)
            assert isinstance(context[dt_field]["time"], str)
            assert isinstance(context[dt_field]["tz"], str)
            assert isinstance(context[dt_field]["datetime"], str)

        # Timezone awareness
        assert context["now"]["tz"]  # Should have timezone offset
        assert context["now_utc"]["tz"] == "+0000"  # UTC always +0000
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

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "scenario,is_available,has_task",
        [
            ("cli_available_enabled", True, True),
            ("cli_available_not_enabled", True, True),
            ("cli_not_available", False, True),
            ("task_not_registered", False, False),
        ],
        ids=["cli_available_enabled", "cli_available_not_enabled", "cli_not_available", "task_not_registered"],
    )
    async def test_openspec_context_scenarios(self, scenario, is_available, has_task) -> None:
        """Test OpenSpec context with various CLI and task registration scenarios."""
        from unittest.mock import patch

        from mcp_guide.openspec.task import OpenSpecTask

        cache = TemplateContextCache()

        if has_task:
            mock_task = Mock(spec=OpenSpecTask)
            mock_task.is_available.return_value = is_available
            mock_task.get_version.return_value = "1.2.3" if is_available else None
            mock_task.get_changes.return_value = []
            mock_task.get_show.return_value = None
            mock_task.get_status.return_value = None
            mock_task.meets_minimum_version.return_value = is_available
        else:
            mock_task = None

        with patch("mcp_guide.task_manager.get_task_manager") as mock_tm:
            mock_tm.return_value.get_task_by_type.return_value = mock_task
            mock_tm.return_value.get_task_statistics.return_value = {}

            context = await cache._build_agent_context()

            if has_task:
                # Task registered, so openspec is truthy (a dict)
                assert context["openspec"]
                assert isinstance(context["openspec"], dict)
            else:
                # When task not registered, openspec is False (disabled)
                assert context["openspec"] is False

    @pytest.mark.anyio
    async def test_build_agent_context_exposes_handoff_and_membership_flags(self) -> None:
        """Test that agent context includes handoff and normalized membership flags."""
        from mcp_guide.agent_detection import AgentInfo

        cache = TemplateContextCache()
        mock_session = Mock()
        mock_session.agent_info = AgentInfo(
            name="Kiro CLI",
            normalized_name="q-dev",
            version="1.0.0",
            prompt_prefix="@",
        )

        with (
            patch("mcp_guide.session.get_active_session", return_value=mock_session),
            patch("mcp_guide.models.resolve_all_flags", return_value={}),
            patch("mcp_guide.task_manager.get_task_manager") as mock_tm,
        ):
            mock_tm.return_value.get_task_statistics.return_value = {}
            mock_tm.return_value.get_task_by_type.return_value = None

            context = await cache._build_agent_context()

            assert context["agent"]["class"] == "q-dev"
            assert context["agent"]["prefix"] == "@"
            assert context["agent"]["has_handoff"] is True
            assert context["agent"]["is_q_dev"] is True
            assert context["agent"]["is_kiro"] is True
            assert context["agent"]["is_codex"] is False

    @pytest.mark.anyio
    async def test_build_agent_context_defaults_unknown_agent_to_no_handoff(self) -> None:
        """Test that non-validated agents default to inline behavior."""
        from mcp_guide.agent_detection import AgentInfo

        cache = TemplateContextCache()
        mock_session = Mock()
        mock_session.agent_info = AgentInfo(
            name="Custom Agent",
            normalized_name="custom-agent",
            version="1.0.0",
            prompt_prefix="/",
        )

        with (
            patch("mcp_guide.session.get_active_session", return_value=mock_session),
            patch("mcp_guide.models.resolve_all_flags", return_value={}),
            patch("mcp_guide.task_manager.get_task_manager") as mock_tm,
        ):
            mock_tm.return_value.get_task_statistics.return_value = {}
            mock_tm.return_value.get_task_by_type.return_value = None

            context = await cache._build_agent_context()

            assert context["agent"]["class"] == "custom-agent"
            assert context["agent"]["has_handoff"] is False
            assert context["agent"]["is_unknown"] is False
            assert context["agent"]["is_codex"] is False

    @pytest.mark.anyio
    async def test_workflow_context_with_phase_booleans(self) -> None:
        """Test workflow context includes phase-specific boolean flags for configured phases."""
        from mcp_guide.models import Project

        cache = TemplateContextCache()

        mock_session = Mock()
        mock_project = Project(name="test-project", key="test", hash="abc123", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)
        mock_session.get_all_projects = AsyncMock(return_value={})
        mock_session.feature_flags = Mock(return_value=Mock(list=AsyncMock(return_value={})))

        mock_workflow_state = Mock(
            phase="implementation",
            issue="test-issue",
            tracking={},
            description="",
            queue=[],
        )

        with (
            patch("mcp_guide.session.get_session", return_value=mock_session),
            patch("mcp_guide.models.resolve_all_flags", return_value={"workflow": True}),
            patch("mcp_guide.task_manager.get_task_manager") as mock_tm,
            patch("mcp_guide.mcp_context.resolve_project_path", return_value="/test/path"),
        ):
            # Configure mock to return workflow_state when called with "workflow_state"
            def get_cached_data_side_effect(key):
                if key == "workflow_state":
                    return mock_workflow_state
                return None

            mock_tm.return_value.get_cached_data.side_effect = get_cached_data_side_effect

            context = await cache._build_project_context()

            assert "workflow" in context
            assert context["workflow"]["phase"] == "implementation"
            # All configured phases should be True
            assert context["workflow"]["discussion"] is True
            assert context["workflow"]["planning"] is True
            assert context["workflow"]["implementation"] is True
            assert context["workflow"]["check"] is True
            assert context["workflow"]["review"] is True

    @pytest.mark.anyio
    async def test_workflow_context_with_consent_structure(self) -> None:
        """Test workflow context includes consent with entry/exit structure."""
        from mcp_guide.models import Project

        cache = TemplateContextCache()

        mock_session = Mock()
        mock_project = Project(name="test-project", key="test", hash="abc123", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)
        mock_session.get_all_projects = AsyncMock(return_value={})
        mock_session.feature_flags = Mock(return_value=Mock(list=AsyncMock(return_value={})))

        mock_workflow_state = Mock(
            phase="discussion",
            issue="test-issue",
            tracking={},
            description="",
            queue=[],
        )

        with (
            patch("mcp_guide.session.get_session", return_value=mock_session),
            patch("mcp_guide.models.resolve_all_flags", return_value={"workflow": True}),
            patch("mcp_guide.task_manager.get_task_manager") as mock_tm,
            patch("mcp_guide.mcp_context.resolve_project_path", return_value="/test/path"),
        ):

            def get_cached_data_side_effect(key):
                if key == "workflow_state":
                    return mock_workflow_state
                return None

            mock_tm.return_value.get_cached_data.side_effect = get_cached_data_side_effect

            context = await cache._build_project_context()

            assert "workflow" in context
            assert "consent" in context["workflow"]
            # Default consent: implementation entry, review exit
            assert context["workflow"]["consent"]["implementation"]["entry"] is True
            assert context["workflow"]["consent"]["implementation"]["exit"] is False
            assert context["workflow"]["consent"]["review"]["entry"] is False
            assert context["workflow"]["consent"]["review"]["exit"] is True
            assert context["workflow"]["consent"]["discussion"]["entry"] is False
            assert context["workflow"]["consent"]["discussion"]["exit"] is False

    @pytest.mark.anyio
    async def test_workflow_context_with_custom_consent(self) -> None:
        """Test workflow context with custom consent configuration."""
        from mcp_guide.models import Project

        cache = TemplateContextCache()

        mock_session = Mock()
        mock_project = Project(name="test-project", key="test", hash="abc123", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)
        mock_session.get_all_projects = AsyncMock(return_value={})
        mock_session.feature_flags = Mock(return_value=Mock(list=AsyncMock(return_value={})))

        mock_workflow_state = Mock(
            phase="planning",
            issue="test-issue",
            tracking={},
            description="",
            queue=[],
        )

        custom_consent = {"planning": ["entry", "exit"], "check": ["entry"]}

        with (
            patch("mcp_guide.session.get_session", return_value=mock_session),
            patch(
                "mcp_guide.models.resolve_all_flags",
                return_value={"workflow": True, "workflow-consent": custom_consent},
            ),
            patch("mcp_guide.task_manager.get_task_manager") as mock_tm,
            patch("mcp_guide.mcp_context.resolve_project_path", return_value="/test/path"),
        ):

            def get_cached_data_side_effect(key):
                if key == "workflow_state":
                    return mock_workflow_state
                return None

            mock_tm.return_value.get_cached_data.side_effect = get_cached_data_side_effect

            context = await cache._build_project_context()

            assert "workflow" in context
            assert "consent" in context["workflow"]
            assert context["workflow"]["consent"]["planning"]["entry"] is True
            assert context["workflow"]["consent"]["planning"]["exit"] is True
            assert context["workflow"]["consent"]["check"]["entry"] is True
            assert context["workflow"]["consent"]["check"]["exit"] is False

    @pytest.mark.anyio
    async def test_workflow_context_with_current_phase_consent(self) -> None:
        """Test workflow context includes current phase consent flags."""
        from mcp_guide.models import Project

        cache = TemplateContextCache()

        mock_session = Mock()
        mock_project = Project(name="test-project", key="test", hash="abc123", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)
        mock_session.get_all_projects = AsyncMock(return_value={})
        mock_session.feature_flags = Mock(return_value=Mock(list=AsyncMock(return_value={})))

        mock_workflow_state = Mock(
            phase="implementation",
            issue="test-issue",
            tracking={},
            description="",
            queue=[],
        )

        with (
            patch("mcp_guide.session.get_session", return_value=mock_session),
            patch("mcp_guide.models.resolve_all_flags", return_value={"workflow": True}),
            patch("mcp_guide.task_manager.get_task_manager") as mock_tm,
            patch("mcp_guide.mcp_context.resolve_project_path", return_value="/test/path"),
        ):

            def get_cached_data_side_effect(key):
                if key == "workflow_state":
                    return mock_workflow_state
                return None

            mock_tm.return_value.get_cached_data.side_effect = get_cached_data_side_effect

            context = await cache._build_project_context()

            assert "workflow" in context
            assert "consent" in context["workflow"]
            # Current phase is implementation, which has entry consent by default
            assert context["workflow"]["consent"]["entry"] is True
            assert context["workflow"]["consent"]["exit"] is False

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("phase", "issue", "expected_next"),
        [
            ("implementation", "test-issue", "check"),
            ("review", "test-issue", "discussion"),
            ("exploration", "explor-test", None),
        ],
        ids=["ordered_next", "ordered_wraparound", "exploration_no_next"],
    )
    async def test_workflow_next_phase_behavior(self, phase: str, issue: str, expected_next: str | None) -> None:
        """Workflow next-phase behavior should reflect ordered and non-ordered phases."""
        from mcp_guide.models import Project

        cache = TemplateContextCache()

        mock_session = Mock()
        mock_project = Project(name="test-project", key="test", hash="abc123", categories={}, collections={})
        mock_session.get_project = AsyncMock(return_value=mock_project)
        mock_session.get_all_projects = AsyncMock(return_value={})
        mock_session.feature_flags = Mock(return_value=Mock(list=AsyncMock(return_value={})))

        mock_workflow_state = Mock(
            phase=phase,
            issue=issue,
            tracking={},
            description="",
            queue=[],
        )

        with (
            patch("mcp_guide.session.get_session", return_value=mock_session),
            patch("mcp_guide.models.resolve_all_flags", return_value={"workflow": True}),
            patch("mcp_guide.task_manager.get_task_manager") as mock_tm,
            patch("mcp_guide.mcp_context.resolve_project_path", return_value="/test/path"),
        ):

            def get_cached_data_side_effect(key):
                if key == "workflow_state":
                    return mock_workflow_state
                return None

            mock_tm.return_value.get_cached_data.side_effect = get_cached_data_side_effect

            context = await cache._build_project_context()

            assert "workflow" in context
            if expected_next is None:
                assert context["workflow"]["next"] is None
            else:
                assert context["workflow"]["next"]["value"] == expected_next

            if phase == "exploration":
                assert context["workflow"]["phases"]["exploration"]["ordered"] is False
                assert "next" not in context["workflow"]["phases"]["exploration"]
                assert context["workflow"]["issue_is_exploratory"] is False
