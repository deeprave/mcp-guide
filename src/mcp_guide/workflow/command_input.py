"""Specialise workflow-command elicitation from project state before it is requested."""

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

WORKFLOW_PHASES_SOURCE = "workflow-phases"


def prepare_command_input(
    forms: Mapping[str, Any],
    context: Mapping[str, Any] | None,
    args: Sequence[str],
    kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fill dynamic choices before generic elicitation resolution."""
    prepared = deepcopy(dict(forms))
    for identifier, form in list(prepared.items()):
        if not isinstance(form, dict):
            continue
        properties = _form_properties(form)
        for definition in properties.values():
            source = _property_source(definition)
            if source == WORKFLOW_PHASES_SOURCE:
                if args or (kwargs is not None and "phase" in kwargs) or not _apply_phase_choices(definition, context):
                    prepared.pop(identifier, None)
                break
    return prepared


def _apply_phase_choices(definition: dict[str, Any], context: Mapping[str, Any] | None) -> bool:
    """Replace a workflow-phase source with the enabled phases other than the active one."""
    choices = _phase_choices(context)
    definition.pop("source", None)
    if not choices:
        return False
    definition["enum"] = choices
    return True


def _phase_choices(context: Mapping[str, Any] | None) -> list[str]:
    """Return enabled workflow phases, omitting the phase that is already active."""
    workflow = context.get("workflow") if isinstance(context, Mapping) else None
    if not isinstance(workflow, Mapping):
        return []
    current = workflow.get("phase")
    current_name = current if isinstance(current, str) else None
    return [name for name in workflow_phase_names(workflow) if name != current_name]


def workflow_phase_names(workflow: Mapping[str, Any]) -> list[str]:
    """Return distinct configured workflow phase names in their declared order."""
    phase_list = workflow.get("phase_list")
    if isinstance(phase_list, Sequence) and not isinstance(phase_list, (str, bytes)):
        names = [
            item if isinstance(item, str) else item.get("value") if isinstance(item, Mapping) else None
            for item in phase_list
        ]
        result = [name for name in names if isinstance(name, str) and name]
        if result:
            return list(dict.fromkeys(result))
    phases = workflow.get("phases")
    if isinstance(phases, Mapping):
        return [name for name in phases if isinstance(name, str)]
    return []


def _form_properties(form: Mapping[str, Any]) -> dict[str, Any]:
    schema = form.get("schema")
    properties = schema.get("properties") if isinstance(schema, Mapping) else None
    if not isinstance(properties, dict):
        return {}
    return properties


def _property_source(definition: object) -> str | None:
    if isinstance(definition, Mapping):
        source = definition.get("source")
        if isinstance(source, str):
            return source
    return None
