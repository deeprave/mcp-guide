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
        "workflow_config,consent_config,expected_phases,expected_permissions",
        [
            # Default workflow with default consent
            (
                None,
                None,
                ["discussion", "planning", "implementation", "check", "review", "default"],
                {
                    "discussion": {"default": True, "pre": False, "post": False},
                    "planning": {"pre": False, "post": False},
                    "implementation": {"pre": True, "post": False},
                    "check": {"pre": False, "post": False},
                    "review": {"pre": False, "post": True},
                    "default": "discussion",
                },
            ),
            # Custom workflow with custom consent
            (
                ["discussion", "planning", "implementation", "check", "review"],
                {"planning": ["entry", "exit"], "check": ["entry"]},
                ["discussion", "planning", "implementation", "check", "review", "default"],
                {
                    "discussion": {"default": True, "pre": False, "post": False},
                    "planning": {"pre": True, "post": True},
                    "implementation": {"pre": False, "post": False},
                    "check": {"pre": True, "post": False},
                    "review": {"pre": False, "post": False},
                    "default": "discussion",
                },
            ),
            # Minimal workflow with no consent
            (
                ["discussion", "implementation"],
                False,
                ["discussion", "implementation", "default"],
                {
                    "discussion": {"default": True, "pre": False, "post": False},
                    "implementation": {"pre": False, "post": False},
                    "default": "discussion",
                },
            ),
            # Custom default phase
            (
                ["planning", "implementation"],
                {"planning": ["entry"]},
                ["planning", "implementation", "default"],
                {
                    "planning": {"default": True, "pre": True, "post": False},
                    "implementation": {"pre": False, "post": False},
                    "default": "planning",
                },
            ),
        ],
    )
    def test_workflow_transitions_configurations(
        self, workflow_config, consent_config, expected_phases, expected_permissions
    ):
        """Test various workflow configurations and their permission metadata."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return workflow_config
            if key == "workflow_consent_flag":
                return consent_config
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        transitions = self.cache._build_workflow_transitions()

        # Verify expected phases
        assert set(transitions.keys()) == set(expected_phases)

        # Verify permissions match expected
        assert transitions == expected_permissions

    @pytest.mark.parametrize(
        "consent_types,expected_pre,expected_post",
        [
            (["entry"], True, False),  # Pre-consent only
            (["exit"], False, True),  # Post-consent only
            (["entry", "exit"], True, True),  # Both consents
            ([], False, False),  # No consent required
        ],
    )
    def test_consent_types(self, consent_types, expected_pre, expected_post):
        """Test various consent type combinations."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return ["discussion", "implementation"]
            if key == "workflow_consent_flag":
                return {"implementation": consent_types}
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        transitions = self.cache._build_workflow_transitions()

        assert transitions["implementation"]["pre"] == expected_pre
        assert transitions["implementation"]["post"] == expected_post

    def test_disabled_workflow(self):
        """Test workflow transitions when workflow is disabled."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return False
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        transitions = self.cache._build_workflow_transitions()

        assert transitions == {}

    def test_fallback_on_parsing_error(self):
        """Test fallback to default when workflow flag parsing fails."""

        def get_cached_data(key):
            if key == "workflow_flag":
                raise Exception("Parse error")
            if key == "workflow_consent_flag":
                return None
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        transitions = self.cache._build_workflow_transitions()

        # Should fall back to default workflow with default consent
        assert "discussion" in transitions
        assert "implementation" in transitions
        assert transitions["discussion"]["default"] is True
        assert transitions["implementation"]["pre"] is True
        assert transitions["review"]["post"] is True

    def test_workflow_structure_validation(self):
        """Test that workflow transitions have correct structure."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return None
            if key == "workflow_consent_flag":
                return None
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

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

    def test_consent_string_normalization(self):
        """Test that single string consent values are normalized to lists."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return ["discussion", "implementation"]
            if key == "workflow_consent_flag":
                # Single string instead of list
                return {"implementation": "entry"}
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        transitions = self.cache._build_workflow_transitions()

        # Should work with single string
        assert transitions["implementation"]["pre"] is True
        assert transitions["implementation"]["post"] is False
