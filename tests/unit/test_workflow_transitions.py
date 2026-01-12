"""Tests for workflow transitions permission metadata."""

from unittest.mock import Mock

import pytest

from mcp_guide.workflow.context import WorkflowContextCache


class TestWorkflowTransitions:
    """Test workflow.transitions permission metadata generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.task_manager = Mock()
        self.cache = WorkflowContextCache(self.task_manager)

    @pytest.mark.parametrize(
        "workflow_config,expected_phases,expected_permissions",
        [
            # Default workflow
            (
                None,
                ["discussion", "planning", "implementation", "check", "review", "default"],
                {
                    "discussion": {"default": True, "pre": False, "post": False},
                    "planning": {"pre": False, "post": False},
                    "implementation": {"pre": True, "post": False},
                    "check": {"pre": False, "post": True},
                    "review": {"pre": False, "post": True},
                    "default": "discussion",
                },
            ),
            # Custom workflow with mixed permissions
            (
                ["discussion", "*planning*", "implementation", "*check", "review*"],
                ["discussion", "planning", "implementation", "check", "review", "default"],
                {
                    "discussion": {"default": True, "pre": False, "post": False},
                    "planning": {"pre": True, "post": True},
                    "implementation": {"pre": False, "post": False},
                    "check": {"pre": True, "post": False},
                    "review": {"pre": False, "post": True},
                    "default": "discussion",
                },
            ),
            # Minimal workflow
            (
                ["discussion", "*implementation"],
                ["discussion", "implementation", "default"],
                {
                    "discussion": {"default": True, "pre": False, "post": False},
                    "implementation": {"pre": True, "post": False},
                    "default": "discussion",
                },
            ),
            # Custom default phase
            (
                ["*planning", "implementation"],
                ["planning", "implementation", "default"],
                {
                    "planning": {"default": True, "pre": True, "post": False},
                    "implementation": {"pre": False, "post": False},
                    "default": "planning",
                },
            ),
        ],
    )
    def test_workflow_transitions_configurations(self, workflow_config, expected_phases, expected_permissions):
        """Test various workflow configurations and their permission metadata."""
        self.task_manager.get_cached_data.return_value = workflow_config

        transitions = self.cache._build_workflow_transitions()

        # Verify expected phases
        assert set(transitions.keys()) == set(expected_phases)

        # Verify permissions match expected
        assert transitions == expected_permissions

    @pytest.mark.parametrize(
        "phase_marker,expected_pre,expected_post",
        [
            ("*implementation", True, False),  # Pre-consent only
            ("implementation*", False, True),  # Post-consent only
            ("*implementation*", True, True),  # Both consents
            ("implementation", False, False),  # No consent required
        ],
    )
    def test_permission_markers(self, phase_marker, expected_pre, expected_post):
        """Test various permission marker combinations."""
        workflow = ["discussion", phase_marker]
        self.task_manager.get_cached_data.return_value = workflow

        transitions = self.cache._build_workflow_transitions()

        clean_phase = phase_marker.strip("*")
        assert transitions[clean_phase]["pre"] == expected_pre
        assert transitions[clean_phase]["post"] == expected_post

    def test_disabled_workflow(self):
        """Test workflow transitions when workflow is disabled."""
        self.task_manager.get_cached_data.return_value = False

        transitions = self.cache._build_workflow_transitions()

        assert transitions == {}

    def test_fallback_on_parsing_error(self):
        """Test fallback to default when workflow flag parsing fails."""
        self.task_manager.get_cached_data.side_effect = Exception("Parse error")

        transitions = self.cache._build_workflow_transitions()

        # Should fall back to default workflow
        assert "discussion" in transitions
        assert "implementation" in transitions
        assert transitions["discussion"]["default"] is True
        assert transitions["implementation"]["pre"] is True

    def test_workflow_structure_validation(self):
        """Test that workflow transitions have correct structure."""
        self.task_manager.get_cached_data.return_value = None

        transitions = self.cache._build_workflow_transitions()

        # Verify structure of each phase (excluding default field)
        for phase, metadata in transitions.items():
            if phase != "default":
                assert "pre" in metadata
                assert "post" in metadata
                assert isinstance(metadata["pre"], bool)
                assert isinstance(metadata["post"], bool)

        # Only one phase should have default: true
        phases_with_default = [
            phase for phase, meta in transitions.items() if phase != "default" and meta.get("default")
        ]
        assert len(phases_with_default) == 1

        # Should have separate default field
        assert "default" in transitions
        assert transitions["default"] == phases_with_default[0]
