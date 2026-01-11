"""Tests for workflow instruction generator functionality."""

from mcp_guide.workflow.change_detection import ChangeEvent, ChangeType
from mcp_guide.workflow.instruction_generator import get_instruction_template_for_change
from mcp_guide.workflow.schema import WorkflowPhase


class TestInstructionGenerator:
    """Test workflow instruction template selection."""

    def test_phase_change_template_selection(self):
        """Test that phase changes use phase-specific templates."""
        change = ChangeEvent(
            change_type=ChangeType.PHASE, from_value=WorkflowPhase.DISCUSSION, to_value=WorkflowPhase.PLANNING
        )

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "*planning"

    def test_issue_change_template_selection(self):
        """Test that issue changes use monitoring-result template."""
        change = ChangeEvent(change_type=ChangeType.ISSUE, from_value="old-issue", to_value="new-issue")

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "monitoring-result"

    def test_tracking_change_template_selection(self):
        """Test that tracking changes use monitoring-result template."""
        change = ChangeEvent(change_type=ChangeType.TRACKING, from_value="PROJ-123", to_value="PROJ-456")

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "monitoring-result"

    def test_description_change_template_selection(self):
        """Test that description changes use monitoring-result template."""
        change = ChangeEvent(
            change_type=ChangeType.DESCRIPTION, from_value="Old description", to_value="New description"
        )

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "monitoring-result"

    def test_queue_change_template_selection(self):
        """Test that queue changes use monitoring-result template."""
        change = ChangeEvent(
            change_type=ChangeType.QUEUE, from_value=["item1"], to_value=["item1", "item2"], added_items=["item2"]
        )

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "monitoring-result"

    def test_phase_change_to_implementation(self):
        """Test phase change to implementation phase."""
        change = ChangeEvent(
            change_type=ChangeType.PHASE, from_value=WorkflowPhase.PLANNING, to_value=WorkflowPhase.IMPLEMENTATION
        )

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "*implementation"

    def test_phase_change_to_review(self):
        """Test phase change to review phase."""
        change = ChangeEvent(
            change_type=ChangeType.PHASE, from_value=WorkflowPhase.CHECK, to_value=WorkflowPhase.REVIEW
        )

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "*review"

    def test_phase_change_with_none_to_value(self):
        """Test phase change with None to_value falls back to monitoring-result."""
        change = ChangeEvent(change_type=ChangeType.PHASE, from_value=WorkflowPhase.REVIEW, to_value=None)

        template_pattern = get_instruction_template_for_change(change)
        assert template_pattern == "monitoring-result"
