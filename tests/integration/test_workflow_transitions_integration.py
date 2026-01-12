"""Integration test for workflow.transitions template variable."""

from unittest.mock import Mock

import pytest

from mcp_guide.workflow.context import WorkflowContextCache
from mcp_guide.workflow.schema import WorkflowPhase, WorkflowState


class TestWorkflowTransitionsIntegration:
    """Integration tests for workflow.transitions in template context."""

    @pytest.mark.asyncio
    async def test_workflow_transitions_in_template_context(self):
        """Test that workflow.transitions is available in template context."""
        # Mock task manager with workflow state
        task_manager = Mock()
        workflow_state = WorkflowState(phase=WorkflowPhase.DISCUSSION, issue="test-issue", tracking="JIRA TEST-123")
        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": workflow_state,
            "workflow_file_path": ".guide.yaml",
            "workflow_flag": None,  # Use default
        }.get(key)

        # Create workflow context cache
        context_cache = WorkflowContextCache(task_manager)

        # Get workflow context
        context = await context_cache.get_workflow_context()

        # Verify workflow.transitions is present
        assert "workflow" in context
        workflow_vars = context["workflow"]
        assert "transitions" in workflow_vars

        transitions = workflow_vars["transitions"]

        # Verify structure matches expected format from proposal
        expected_phases = ["discussion", "planning", "implementation", "check", "review", "default"]
        assert set(transitions.keys()) == set(expected_phases)

        # Verify each phase has required metadata (excluding default field)
        for phase_name, metadata in transitions.items():
            if phase_name != "default":
                assert "pre" in metadata
                assert "post" in metadata
                assert isinstance(metadata["pre"], bool)
                assert isinstance(metadata["post"], bool)
                # Only discussion phase should have default: true
                if phase_name == "discussion":
                    assert metadata.get("default", False) is True
                else:
                    assert "default" not in metadata

        # Verify default field exists and points to discussion
        assert transitions["default"] == "discussion"
        assert transitions["implementation"]["pre"] is True
        assert transitions["review"]["post"] is True

    @pytest.mark.asyncio
    async def test_workflow_transitions_with_custom_phases(self):
        """Test workflow.transitions with custom phase configuration."""
        # Mock task manager with custom workflow flag
        task_manager = Mock()
        workflow_state = WorkflowState(phase=WorkflowPhase.DISCUSSION)
        custom_phases = ["discussion", "*planning", "implementation*"]

        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": workflow_state,
            "workflow_flag": custom_phases,
        }.get(key)

        context_cache = WorkflowContextCache(task_manager)
        context = await context_cache.get_workflow_context()

        transitions = context["workflow"]["transitions"]

        # Should only have custom phases plus default field
        assert set(transitions.keys()) == {"discussion", "planning", "implementation", "default"}

        # Verify custom permissions
        assert transitions["planning"]["pre"] is True  # *planning
        assert transitions["planning"]["post"] is False

        assert transitions["implementation"]["pre"] is False
        assert transitions["implementation"]["post"] is True  # implementation*

    @pytest.mark.asyncio
    async def test_workflow_transitions_empty_when_disabled(self):
        """Test workflow.transitions is empty when workflow is disabled."""
        task_manager = Mock()
        task_manager.get_cached_data.side_effect = lambda key: {
            "workflow_state": None,
            "workflow_flag": False,  # Disabled
        }.get(key)

        context_cache = WorkflowContextCache(task_manager)
        context = await context_cache.get_workflow_context()

        # Should have empty transitions when workflow is disabled
        assert context["workflow"]["transitions"] == {}
