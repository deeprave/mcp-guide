"""Tests for workflow phases, next, and consent metadata."""

from unittest.mock import Mock

import pytest

from mcp_guide.workflow.context import WorkflowContextCache
from mcp_guide.workflow.schema import WorkflowState


class TestWorkflowPhases:
    """Test workflow.phases, workflow.next, and workflow.consent generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.task_manager = Mock()
        self.cache = WorkflowContextCache(self.task_manager)

    @pytest.mark.parametrize(
        "workflow_config,consent_config,current_phase,expected_next,expected_consent",
        [
            # Default workflow in discussion phase
            (
                None,
                None,
                "discussion",
                {"value": "planning"},
                {"implementation": True, "review": True},  # Phase-specific flags for phases with consent
            ),
            # Default workflow in planning phase (next is implementation with entry consent)
            (
                None,
                None,
                "planning",
                {"value": "implementation", "consent": {"entry": True}},
                {"exit": True, "implementation": True, "review": True},  # Exit set because next has entry
            ),
            # Default workflow in implementation phase
            (
                None,
                None,
                "implementation",
                {"value": "check"},
                {"entry": True, "implementation": True, "review": True},  # Entry consent for implementation
            ),
            # Default workflow in review phase (has exit consent)
            (
                None,
                None,
                "review",
                {"value": "discussion"},
                {"exit": True, "implementation": True, "review": True},
            ),
            # Custom consent: planning has both entry and exit
            (
                ["discussion", "planning", "implementation"],
                {"planning": ["entry", "exit"]},
                "discussion",
                {"value": "planning", "consent": {"entry": True, "exit": True}},  # Planning has both
                {"exit": True, "planning": True},  # Exit set because next has entry
            ),
            # No consent workflow
            (
                ["discussion", "implementation"],
                False,
                "discussion",
                {"value": "implementation"},
                {},  # No consent requirements
            ),
        ],
    )
    def test_workflow_phases_configurations(
        self, workflow_config, consent_config, current_phase, expected_next, expected_consent
    ):
        """Test various workflow configurations and their phase/consent metadata."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return workflow_config
            if key == "workflow_consent_flag":
                return consent_config
            if key == "workflow_state":
                return WorkflowState(
                    phase=current_phase, issue=None, plan=None, tracking=None, description=None, queue=[]
                )
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        phases, next_phase, consent = self.cache._build_workflow_phases()

        # Verify next phase structure
        assert next_phase == expected_next

        # Verify consent structure
        assert consent == expected_consent

    def test_phases_structure(self):
        """Test that workflow.phases has correct structure with next phase info."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return ["discussion", "planning", "implementation"]
            if key == "workflow_consent_flag":
                return None
            if key == "workflow_state":
                return WorkflowState(
                    phase="discussion", issue=None, plan=None, tracking=None, description=None, queue=[]
                )
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        phases, _, _ = self.cache._build_workflow_phases()

        # Verify each phase has next field
        assert phases["discussion"]["next"] == "planning"
        assert phases["planning"]["next"] == "implementation"
        assert phases["implementation"]["next"] == "discussion"  # Wraps around

    def test_consent_propagation(self):
        """Test that next phase entry consent sets current phase exit consent."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return ["discussion", "planning", "implementation"]
            if key == "workflow_consent_flag":
                # Planning has entry consent
                return {"planning": ["entry"]}
            if key == "workflow_state":
                # Current phase is discussion, next is planning (with entry consent)
                return WorkflowState(
                    phase="discussion", issue=None, plan=None, tracking=None, description=None, queue=[]
                )
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        _, next_phase, consent = self.cache._build_workflow_phases()

        # Next phase should have entry consent
        assert next_phase["consent"]["entry"] is True

        # Current phase should have exit consent (propagated from next entry)
        assert consent["exit"] is True

    def test_disabled_workflow(self):
        """Test workflow phases when workflow is disabled."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return False
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        phases, next_phase, consent = self.cache._build_workflow_phases()

        assert phases == {}
        assert next_phase == {}
        assert consent == {}

    def test_consent_only_when_required(self):
        """Test that consent dict only contains truthy values."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return ["discussion", "implementation"]
            if key == "workflow_consent_flag":
                # Only implementation has entry consent
                return {"implementation": ["entry"]}
            if key == "workflow_state":
                return WorkflowState(
                    phase="discussion", issue=None, plan=None, tracking=None, description=None, queue=[]
                )
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        _, next_phase, consent = self.cache._build_workflow_phases()

        # Next phase should have consent dict with entry
        assert "consent" in next_phase
        assert next_phase["consent"]["entry"] is True
        # Should not have exit key since it's not required
        assert "exit" not in next_phase["consent"]

        # Current phase should have exit (propagated) and implementation flag
        assert consent["exit"] is True
        assert consent["implementation"] is True
        # Should not have entry key since discussion doesn't require it
        assert "entry" not in consent

    def test_consent_string_normalization(self):
        """Test that single string consent values are normalized to lists."""

        def get_cached_data(key):
            if key == "workflow_flag":
                return ["discussion", "implementation"]
            if key == "workflow_consent_flag":
                # Single string instead of list
                return {"implementation": "entry"}
            if key == "workflow_state":
                return WorkflowState(
                    phase="discussion", issue=None, plan=None, tracking=None, description=None, queue=[]
                )
            return None

        self.task_manager.get_cached_data.side_effect = get_cached_data

        _, next_phase, consent = self.cache._build_workflow_phases()

        # Should work with single string
        assert next_phase["consent"]["entry"] is True
        assert consent["exit"] is True  # Propagated from next entry
