"""Fill dynamic elicitation choices from project state before a form is requested."""

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from typing import Any

from mcp_guide.core.mcp_log import get_logger

logger = get_logger(__name__)

WORKFLOW_PHASES_SOURCE = "workflow-phases"
PROJECT_CATEGORIES_SOURCE = "project-categories"
PROJECT_COLLECTIONS_SOURCE = "project-collections"


def prepare_form_sources(
    forms: Mapping[str, Any],
    context: Mapping[str, Any] | None,
    args: Sequence[str] = (),
    kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fill dynamic choices before generic elicitation resolution.

    A property marked with ``source`` receives an ``enum`` built from project state and the marker
    is removed before delivery. A form is omitted when its value was already supplied (positional
    argument or keyword) or when its source has no choices, so the entrypoint's own validation
    reports the missing value. Skills have no positional arguments and pass none.
    """
    prepared = deepcopy(dict(forms))
    for identifier, form in list(prepared.items()):
        if not isinstance(form, dict):
            continue
        properties = _form_properties(form)
        sourced = {name: _property_source(definition) for name, definition in properties.items()}
        sourced = {name: source for name, source in sourced.items() if source is not None}
        if not sourced:
            continue
        supplied = bool(args) or (kwargs is not None and any(_is_supplied(kwargs.get(name)) for name in sourced))
        if supplied or not all([_apply_choices(properties[name], source, context) for name, source in sourced.items()]):
            prepared.pop(identifier, None)
    return prepared


def _is_supplied(value: object) -> bool:
    """Return whether a keyword carries a value; ``0`` and ``False`` count, ``None`` and blank text do not."""
    return value is not None and not (isinstance(value, str) and not value.strip())


def _apply_choices(definition: dict[str, Any], source: str, context: Mapping[str, Any] | None) -> bool:
    """Replace a source marker with its current choices; return whether any choice exists."""
    definition.pop("source", None)
    resolver = _SOURCES.get(source)
    if resolver is None:
        logger.warning("Unknown elicitation source %r; leaving the property as free text", source)
        return True
    choices = resolver(context)
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


def _project_names(context: Mapping[str, Any] | None, key: str) -> list[str]:
    """Return the distinct names of the bound project's categories or collections."""
    project = context.get("project") if isinstance(context, Mapping) else None
    items = project.get(key) if isinstance(project, Mapping) else None
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return []
    names = [item.get("name") for item in items if isinstance(item, Mapping)]
    return list(dict.fromkeys(name for name in names if isinstance(name, str) and name))


def _category_choices(context: Mapping[str, Any] | None) -> list[str]:
    return _project_names(context, "categories")


def _collection_choices(context: Mapping[str, Any] | None) -> list[str]:
    return _project_names(context, "collections")


_SOURCES: dict[str, Callable[[Mapping[str, Any] | None], list[str]]] = {
    WORKFLOW_PHASES_SOURCE: _phase_choices,
    PROJECT_CATEGORIES_SOURCE: _category_choices,
    PROJECT_COLLECTIONS_SOURCE: _collection_choices,
}


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
