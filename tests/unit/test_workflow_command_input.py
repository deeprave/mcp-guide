"""Workflow command input specialisation."""

from mcp_guide.render.context import TemplateContext
from mcp_guide.workflow.command_input import prepare_command_input, workflow_phase_names


def _phase_form() -> dict:
    return {
        "workflow-phase": {
            "message": "Choose the phase to enter.",
            "fallback": "render",
            "schema": {
                "type": "object",
                "properties": {"phase": {"type": "string", "source": "workflow-phases"}},
                "required": ["phase"],
            },
        }
    }


def _workflow_context(*phases: str, current: str | None = None) -> TemplateContext:
    workflow: dict = {"phase_list": list(phases)}
    if current is not None:
        workflow["phase"] = current
    return TemplateContext({"workflow": workflow})


def test_phase_choices_omit_the_active_phase_and_explicit_inputs():
    """Enabled phases become the choice list, without the phase already in effect."""
    forms = prepare_command_input(
        _phase_form(),
        _workflow_context("discussion", "planning", "review", current="planning"),
        [],
    )

    assert forms["workflow-phase"]["schema"]["properties"]["phase"]["enum"] == ["discussion", "review"]
    assert "source" not in forms["workflow-phase"]["schema"]["properties"]["phase"]

    supplied = prepare_command_input(
        _phase_form(),
        _workflow_context("discussion", "planning", current="discussion"),
        ["planning"],
    )
    assert supplied == {}

    explicit_keyword = prepare_command_input(
        _phase_form(),
        _workflow_context("discussion", "planning", current="planning"),
        [],
        {"phase": "planning"},
    )
    assert explicit_keyword == {}


def test_phase_form_is_omitted_when_no_other_phase_is_enabled():
    """A project already on its only enabled phase is not asked to choose it again."""
    forms = prepare_command_input(
        _phase_form(),
        _workflow_context("discussion", current="discussion"),
        [],
    )

    assert forms == {}


def test_workflow_phase_names_preserve_declared_order_and_mapping_fallback():
    """The shared phase helper provides one canonical normalised phase sequence."""
    assert workflow_phase_names({"phase_list": [{"value": "discussion"}, "planning", "planning"]}) == [
        "discussion",
        "planning",
    ]
    assert workflow_phase_names({"phases": {"discussion": {}, "review": {}}}) == ["discussion", "review"]
