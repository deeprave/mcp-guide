"""Integration test for workflow.phases, workflow.next, and workflow.consent template variables."""

from unittest.mock import Mock

import pytest

from mcp_guide.workflow.constants import PHASE_DISCUSSION, PHASE_PLANNING
from mcp_guide.workflow.context import WorkflowContextCache
from mcp_guide.workflow.schema import WorkflowState


class TestWorkflowPhasesIntegration:
    """Integration tests for workflow.phases, workflow.next, and workflow.consent in template context."""

    @pytest.mark.asyncio
    async def test_workflow_phases_in_template_context(self):
        """Test that workflow.phases, workflow.next, and workflow.consent are available in template context."""
        # Mock task manager with workflow state
        task_manager = Mock()
        workflow_state = WorkflowState(phase=PHASE_DISCUSSION, issue="test-issue", tracking="JIRA TEST-123")
        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": workflow_state,
            "workflow_file_path": ".guide.yaml",
            "workflow_flag": None,  # Use default
            "workflow_consent_flag": None,  # Use default
        }.get(key)

        # Create workflow context cache
        context_cache = WorkflowContextCache(task_manager)

        # Get workflow context
        context = await context_cache.get_workflow_context()

        # Verify workflow variables are present
        assert "workflow" in context
        workflow_vars = context["workflow"]
        assert "phases" in workflow_vars
        assert "next" in workflow_vars
        assert "consent" in workflow_vars

        phases = workflow_vars["phases"]
        next_phase = workflow_vars["next"]
        consent = workflow_vars["consent"]

        # Verify phases structure - each phase has next field
        expected_phases = ["discussion", "planning", "implementation", "check", "review"]
        assert set(phases.keys()) == set(expected_phases)
        for phase_name in expected_phases:
            assert "next" in phases[phase_name]

        # Verify next phase structure
        assert "value" in next_phase
        assert next_phase["value"] == "planning"  # discussion -> planning

        # Verify consent structure - should have phase-specific flags
        assert "implementation" in consent  # implementation has entry consent
        assert "review" in consent  # review has exit consent

    @pytest.mark.asyncio
    async def test_workflow_next_with_consent(self):
        """Test workflow.next includes consent when next phase requires it."""
        # Mock task manager - planning phase, next is implementation (has entry consent)
        task_manager = Mock()
        workflow_state = WorkflowState(phase=PHASE_PLANNING)
        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": workflow_state,
            "workflow_flag": None,  # Use default
            "workflow_consent_flag": None,  # Use default
        }.get(key)

        context_cache = WorkflowContextCache(task_manager)
        context = await context_cache.get_workflow_context()

        next_phase = context["workflow"]["next"]
        consent = context["workflow"]["consent"]

        # Next phase should have consent dict with entry
        assert "consent" in next_phase
        assert next_phase["consent"]["entry"] is True

        # Current phase should have exit consent (propagated from next entry)
        assert consent["exit"] is True

    @pytest.mark.asyncio
    async def test_workflow_consent_propagation(self):
        """Test that next phase entry consent sets current phase exit consent."""
        # Mock task manager - discussion phase, next is planning with entry consent
        task_manager = Mock()
        workflow_state = WorkflowState(phase=PHASE_DISCUSSION)
        custom_consent = {"planning": ["entry"]}
        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": workflow_state,
            "workflow_flag": None,
            "workflow_consent_flag": custom_consent,
        }.get(key)

        context_cache = WorkflowContextCache(task_manager)
        context = await context_cache.get_workflow_context()

        next_phase = context["workflow"]["next"]
        consent = context["workflow"]["consent"]

        # Next phase should have entry consent
        assert next_phase["consent"]["entry"] is True

        # Current phase should have exit consent (propagated)
        assert consent["exit"] is True

    @pytest.mark.asyncio
    async def test_workflow_phases_with_custom_config(self):
        """Test workflow.phases with custom phase configuration."""
        # Mock task manager with custom workflow flag and consent
        task_manager = Mock()
        workflow_state = WorkflowState(phase=PHASE_DISCUSSION)
        custom_phases = ["discussion", "planning", "implementation"]
        custom_consent = {"planning": ["entry"], "implementation": ["exit"]}

        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": workflow_state,
            "workflow_flag": custom_phases,
            "workflow_consent_flag": custom_consent,
        }.get(key)

        context_cache = WorkflowContextCache(task_manager)
        context = await context_cache.get_workflow_context()

        phases = context["workflow"]["phases"]
        next_phase = context["workflow"]["next"]
        consent = context["workflow"]["consent"]

        # Should only have custom phases
        assert set(phases.keys()) == {"discussion", "planning", "implementation"}

        # Verify next phase has entry consent
        assert next_phase["value"] == "planning"
        assert next_phase["consent"]["entry"] is True

        # Verify consent has phase-specific flags
        assert consent["planning"] is True
        assert consent["implementation"] is True

    @pytest.mark.asyncio
    async def test_workflow_phases_empty_when_disabled(self):
        """Test workflow.phases/next/consent are empty when workflow is disabled."""
        task_manager = Mock()
        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": None,
            "workflow_flag": False,  # Disabled
        }.get(key)

        context_cache = WorkflowContextCache(task_manager)
        context = await context_cache.get_workflow_context()

        # Should have empty dicts when workflow is disabled
        assert context["workflow"]["phases"] == {}
        assert context["workflow"]["next"] == {}
        assert context["workflow"]["consent"] == {}
