"""Unit tests for workflow transitions functionality."""

from unittest.mock import Mock

from mcp_guide.workflow.context import WorkflowContextCache


class TestWorkflowTransitions:
    """Test workflow transitions template variable generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.task_manager = Mock()
        self.cache = WorkflowContextCache(self.task_manager)

    def test_build_workflow_transitions_default_workflow(self):
        """Test workflow transitions with default workflow configuration."""
        # Mock task manager to return default workflow
        self.task_manager.get_cached_data.return_value = None

        # Call the method
        transitions = self.cache._build_workflow_transitions()

        # Verify structure matches specification
        expected = {
            "discussion": {"default": True, "pre": False, "post": False},
            "planning": {"pre": False, "post": False},
            "implementation": {"pre": True, "post": False},
            "check": {"pre": False, "post": True},
            "review": {"pre": False, "post": True},
            "default": "discussion",
        }

        assert transitions == expected

    def test_build_workflow_transitions_custom_workflow(self):
        """Test workflow transitions with custom workflow configuration."""
        # Mock custom workflow with permission markers
        custom_workflow = ["discussion", "*planning*", "implementation", "*check", "review*"]
        self.task_manager.get_cached_data.return_value = custom_workflow

        transitions = self.cache._build_workflow_transitions()

        expected = {
            "discussion": {"default": True, "pre": False, "post": False},
            "planning": {"pre": True, "post": True},
            "implementation": {"pre": False, "post": False},
            "check": {"pre": True, "post": False},
            "review": {"pre": False, "post": True},
            "default": "discussion",
        }

        assert transitions == expected

    def test_build_workflow_transitions_minimal_workflow(self):
        """Test workflow transitions with minimal workflow."""
        # Mock minimal workflow (discussion + implementation only)
        minimal_workflow = ["discussion", "*implementation"]
        self.task_manager.get_cached_data.return_value = minimal_workflow

        transitions = self.cache._build_workflow_transitions()

        expected = {
            "discussion": {"default": True, "pre": False, "post": False},
            "implementation": {"pre": True, "post": False},
            "default": "discussion",
        }

        assert transitions == expected

    def test_build_workflow_transitions_disabled_workflow(self):
        """Test workflow transitions when workflow is disabled."""
        # Mock disabled workflow
        self.task_manager.get_cached_data.return_value = False

        transitions = self.cache._build_workflow_transitions()

        # Should return empty dict when workflow is disabled
        assert transitions == {}

    def test_build_workflow_transitions_parsing_error(self):
        """Test workflow transitions with parsing error fallback."""
        # Mock task manager to raise exception
        self.task_manager.get_cached_data.side_effect = Exception("Parse error")

        transitions = self.cache._build_workflow_transitions()

        # Should fall back to default workflow
        assert "discussion" in transitions
        assert "implementation" in transitions
        assert transitions["discussion"]["default"] is True
        assert transitions["implementation"]["pre"] is True

    def test_workflow_transitions_only_discussion_has_default_true(self):
        """Test that only discussion phase has default: true."""
        self.task_manager.get_cached_data.return_value = None

        transitions = self.cache._build_workflow_transitions()

        # Only discussion should have default: true
        phases_with_default = [
            phase for phase, meta in transitions.items() if phase != "default" and meta.get("default")
        ]
        assert phases_with_default == ["discussion"]

        # Other phases should not have default key at all (optimized structure)
        for phase, meta in transitions.items():
            if phase not in ["discussion", "default"]:
                assert "default" not in meta

        # Should also have separate default field
        assert transitions["default"] == "discussion"

    def test_workflow_transitions_permission_markers(self):
        """Test various permission marker combinations."""
        test_cases = [
            ("*implementation", True, False),  # Pre-consent only
            ("implementation*", False, True),  # Post-consent only
            ("*implementation*", True, True),  # Both consents
            ("implementation", False, False),  # No consent required
        ]

        for phase_marker, expected_pre, expected_post in test_cases:
            workflow = ["discussion", phase_marker]
            self.task_manager.get_cached_data.return_value = workflow

            transitions = self.cache._build_workflow_transitions()

            # Extract clean phase name for testing
            clean_phase = phase_marker.strip("*")
            assert transitions[clean_phase]["pre"] == expected_pre
            assert transitions[clean_phase]["post"] == expected_post

    def test_workflow_transitions_default_phase_convenience_field(self):
        """Test that workflow.transitions.default returns the default phase name."""
        self.task_manager.get_cached_data.return_value = None

        transitions = self.cache._build_workflow_transitions()

        # Should have a 'default' key that returns the default phase name
        assert "default" in transitions
        assert transitions["default"] == "discussion"

        # Test with custom workflow where planning is the default
        custom_workflow = ["*planning", "implementation"]
        self.task_manager.get_cached_data.return_value = custom_workflow

        transitions = self.cache._build_workflow_transitions()

        # Planning should be marked as default (first phase)
        assert transitions["default"] == "planning"
