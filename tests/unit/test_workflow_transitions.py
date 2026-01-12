"""Tests for workflow transitions permission metadata."""

from unittest.mock import Mock

from mcp_guide.workflow.context import WorkflowContextCache


class TestWorkflowTransitions:
    """Test workflow.transitions permission metadata generation."""

    def test_build_workflow_transitions_default_config(self):
        """Test workflow transitions with default configuration."""
        # Mock task manager
        task_manager = Mock()
        task_manager.get_cached_data.return_value = None

        # Create workflow context cache
        context_cache = WorkflowContextCache(task_manager)

        # Test transitions generation
        transitions = context_cache._build_workflow_transitions()

        # Verify all expected phases are present plus default field
        expected_phases = ["discussion", "planning", "implementation", "check", "review", "default"]
        assert set(transitions.keys()) == set(expected_phases)

        # Verify structure of each phase (excluding default field)
        for phase, metadata in transitions.items():
            if phase != "default":
                assert "pre" in metadata
                assert "post" in metadata
                assert isinstance(metadata["pre"], bool)
                assert isinstance(metadata["post"], bool)
                # Only discussion phase should have default: true
                if phase == "discussion":
                    assert metadata.get("default", False) is True
                else:
                    assert "default" not in metadata

        # Verify default field exists and points to discussion
        assert transitions["default"] == "discussion"

    def test_default_workflow_permissions(self):
        """Test specific permission settings for default workflow."""
        task_manager = Mock()
        task_manager.get_cached_data.return_value = None

        context_cache = WorkflowContextCache(task_manager)
        transitions = context_cache._build_workflow_transitions()

        # Discussion is the default starting phase
        assert transitions["discussion"].get("default", False) is True
        assert transitions["discussion"]["pre"] is False
        assert transitions["discussion"]["post"] is False

        # Planning has no restrictions
        assert "default" not in transitions["planning"]
        assert transitions["planning"]["pre"] is False
        assert transitions["planning"]["post"] is False

        # Implementation requires entry consent (*implementation)
        assert "default" not in transitions["implementation"]
        assert transitions["implementation"]["pre"] is True
        assert transitions["implementation"]["post"] is False

        # Check requires exit consent (check*)
        assert "default" not in transitions["check"]
        assert transitions["check"]["pre"] is False
        assert transitions["check"]["post"] is True

        # Review requires exit consent (review*)
        assert "default" not in transitions["review"]
        assert transitions["review"]["pre"] is False
        assert transitions["review"]["post"] is True

    def test_custom_workflow_permissions(self):
        """Test workflow transitions with custom phase configuration."""
        task_manager = Mock()
        # Mock custom workflow flag with different permissions
        custom_phases = ["discussion", "*planning*", "implementation"]
        task_manager.get_cached_data.return_value = custom_phases

        context_cache = WorkflowContextCache(task_manager)
        transitions = context_cache._build_workflow_transitions()

        # Should only have the configured phases plus default field
        assert set(transitions.keys()) == {"discussion", "planning", "implementation", "default"}

        # Planning should require both entry and exit consent (*planning*)
        assert transitions["planning"]["pre"] is True
        assert transitions["planning"]["post"] is True

        # Implementation should have no restrictions (no markers)
        assert transitions["implementation"]["pre"] is False
        assert transitions["implementation"]["post"] is False

    def test_disabled_workflow(self):
        """Test workflow transitions when workflow is disabled."""
        task_manager = Mock()
        task_manager.get_cached_data.return_value = False  # Disabled workflow

        context_cache = WorkflowContextCache(task_manager)
        transitions = context_cache._build_workflow_transitions()

        # Should return empty dict when workflow is disabled
        assert transitions == {}

    def test_fallback_on_parsing_error(self):
        """Test fallback to default when workflow flag parsing fails."""
        task_manager = Mock()
        # Mock invalid workflow flag that would cause parsing error
        task_manager.get_cached_data.return_value = "invalid_phase_name"

        context_cache = WorkflowContextCache(task_manager)
        transitions = context_cache._build_workflow_transitions()

        # Should fallback to default workflow phases plus default field
        expected_phases = ["discussion", "planning", "implementation", "check", "review", "default"]
        assert set(transitions.keys()) == set(expected_phases)

        # Should have default permissions
        assert transitions["implementation"]["pre"] is True
        assert transitions["review"]["post"] is True
