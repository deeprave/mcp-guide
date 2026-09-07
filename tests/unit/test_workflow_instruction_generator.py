"""Workflow changes select phase-specific or general monitoring guidance."""

import pytest

from mcp_guide.workflow.change_detection import ChangeEvent, ChangeType
from mcp_guide.workflow.instruction_generator import get_instruction_template_for_change


@pytest.mark.parametrize(
    "phase,expected",
    [
        ("planning", "*planning"),
        ("implementation", "*implementation"),
        ("review", "*review"),
        (None, "monitoring-result"),
    ],
    ids=["planning", "implementation", "review", "no-target"],
)
def test_phase_changes_select_target_guidance(phase, expected):
    change = ChangeEvent(change_type=ChangeType.PHASE, from_value="discussion", to_value=phase)
    assert get_instruction_template_for_change(change) == expected


def test_non_phase_changes_select_monitoring_guidance():
    for kind in (ChangeType.ISSUE, ChangeType.TRACKING, ChangeType.DESCRIPTION, ChangeType.QUEUE):
        change = ChangeEvent(change_type=kind, from_value=None, to_value=None)
        assert get_instruction_template_for_change(change) == "monitoring-result", kind
