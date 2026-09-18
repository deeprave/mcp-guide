"""Frontmatter-declared MCP elicitation for Guide skill entrypoints."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from fastmcp import Context
from fastmcp.server.elicitation import AcceptedElicitation, CancelledElicitation
from mcp_types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult
from pydantic import BaseModel, create_model

from mcp_guide.result import Result

_PRIMITIVE_TYPES: dict[str, type[bool] | type[float] | type[int] | type[str]] = {
    "boolean": bool,
    "integer": int,
    "number": float,
    "string": str,
}


@dataclass(frozen=True)
class SkillElicitation:
    """One frontmatter-declared form required before rendering a skill entrypoint."""

    identifier: str
    message: str
    schema: dict[str, Any]
    fallback: str

    @property
    def required_fields(self) -> tuple[str, ...]:
        """Return query keywords that satisfy this form when supplied explicitly."""
        return tuple(cast(list[str], self.schema.get("required", [])))


class ResolvedSkillKeywords(dict[str, Any]):
    """Rendered template keywords, including forms satisfied by safe defaults."""

    def __init__(self, values: Mapping[str, Any], *, defaulted_forms: frozenset[str] = frozenset()) -> None:
        super().__init__(values)
        self.defaulted_forms = defaulted_forms


def _failure(message: str) -> Result[Any]:
    """Create a consistent skill-frontmatter validation failure."""
    return Result.failure(f"Invalid skill elicitation frontmatter: {message}")


def _is_primitive(value: object) -> bool:
    """Return whether a value is supported by MCP's primitive form fields."""
    return isinstance(value, (str, int, float, bool)) and not isinstance(value, complex)


def _is_valid_field_value(definition: Mapping[str, Any], value: object) -> bool:
    """Return whether one primitive value satisfies an elicitation property definition."""
    expected_type = _PRIMITIVE_TYPES[cast(str, definition["type"])]
    valid = (
        isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected_type in {int, float}
        else isinstance(value, expected_type)
    )
    enum = definition.get("enum")
    return valid and (enum is None or value in enum)


def _validate_schema(identifier: str, value: object) -> SkillElicitation | Result[Any]:
    """Validate one declarative form without interpreting a skill-specific meaning."""
    if not isinstance(value, Mapping):
        return _failure(f"'{identifier}' must be a mapping")
    message = value.get("message")
    schema = value.get("schema")
    fallback = value.get("fallback", "error")
    if not isinstance(message, str) or not message.strip():
        return _failure(f"'{identifier}.message' must be a non-empty string")
    if not isinstance(schema, Mapping) or schema.get("type") != "object":
        return _failure(f"'{identifier}.schema' must be an object schema")
    if fallback not in {"error", "render"}:
        return _failure(f"'{identifier}.fallback' must be 'error' or 'render'")
    properties = schema.get("properties")
    required = schema.get("required", [])
    if not isinstance(properties, Mapping) or not properties:
        return _failure(f"'{identifier}.schema.properties' must be a non-empty mapping")
    if not isinstance(required, list) or not all(isinstance(field, str) for field in required):
        return _failure(f"'{identifier}.schema.required' must be a list of field names")
    if not set(required).issubset(properties):
        return _failure(f"'{identifier}.schema.required' must name declared properties")
    for field, definition in properties.items():
        if not isinstance(field, str) or not field:
            return _failure(f"'{identifier}.schema.properties' contains an invalid field name")
        if not isinstance(definition, Mapping) or definition.get("type") not in _PRIMITIVE_TYPES:
            return _failure(f"'{identifier}.schema.properties.{field}' must use a primitive MCP type")
        enum = definition.get("enum")
        if enum is not None and (
            not isinstance(enum, list) or not enum or not all(_is_primitive(item) for item in enum)
        ):
            return _failure(f"'{identifier}.schema.properties.{field}.enum' must contain primitive values")
        if "default" in definition and not _is_valid_field_value(definition, definition["default"]):
            return _failure(f"'{identifier}.schema.properties.{field}.default' must match its field definition")
    return SkillElicitation(identifier=identifier, message=message, schema=dict(schema), fallback=fallback)


def parse_skill_elicitations(frontmatter: Mapping[str, Any]) -> tuple[SkillElicitation, ...] | Result[Any]:
    """Read generic entrypoint forms from a selected skill's frontmatter."""
    raw_elicitations = frontmatter.get("elicitation")
    if raw_elicitations is None:
        return ()
    if not isinstance(raw_elicitations, Mapping):
        return _failure("'elicitation' must be a mapping of form names")

    elicitations: list[SkillElicitation] = []
    declared_fields: set[str] = set()
    for identifier, value in raw_elicitations.items():
        if not isinstance(identifier, str) or not identifier:
            return _failure("form names must be non-empty strings")
        elicitation = _validate_schema(identifier, value)
        if isinstance(elicitation, Result):
            return elicitation
        duplicate_fields = declared_fields.intersection(elicitation.schema["properties"])
        if duplicate_fields:
            return _failure(f"forms must not share fields: {', '.join(sorted(duplicate_fields))}")
        declared_fields.update(elicitation.schema["properties"])
        elicitations.append(elicitation)
    return tuple(elicitations)


def _required_fields_missing(elicitation: SkillElicitation, kwargs: Mapping[str, Any]) -> bool:
    """Return whether explicit URI keywords leave a required form field unresolved."""
    return any(
        field not in kwargs or kwargs[field] is None or (isinstance(kwargs[field], str) and not kwargs[field].strip())
        for field in elicitation.required_fields
    )


def _input_request(elicitations: tuple[SkillElicitation, ...]) -> InputRequiredResult:
    """Return one standards-compliant request containing all missing forms."""
    return InputRequiredResult(
        input_requests={
            elicitation.identifier: ElicitRequest(
                params=ElicitRequestFormParams(
                    message=elicitation.message,
                    requested_schema=elicitation.schema,
                )
            )
            for elicitation in elicitations
        },
        request_state="skill-elicitation",
    )


def _client_supports_elicitation(mcp_context: Context) -> bool:
    """Return whether the connected client negotiated MCP elicitation."""
    session = getattr(mcp_context, "session", None)
    client_params = getattr(session, "client_params", None)
    capabilities = getattr(client_params, "capabilities", None)
    return getattr(capabilities, "elicitation", None) is not None


def _selection_from_response(
    elicitation: SkillElicitation, response: object
) -> dict[str, str | bool | float | int] | Result[Any]:
    """Validate one completed form against its declared primitive schema."""
    if getattr(response, "action", None) != "accept":
        return Result.failure(f"Skill input '{elicitation.identifier}' was not completed.")
    content = getattr(response, "content", None)
    if not isinstance(content, Mapping):
        return Result.failure(f"Skill input '{elicitation.identifier}' did not return form values.")

    values: dict[str, str | bool | float | int] = {}
    properties = cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    for field, definition in properties.items():
        value = content.get(field)
        if field in elicitation.required_fields and (
            field not in content or value is None or (isinstance(value, str) and not value.strip())
        ):
            return Result.failure(f"Skill input '{elicitation.identifier}' requires '{field}'.")
        if value is None:
            continue
        if not _is_valid_field_value(definition, value):
            return Result.failure(f"Skill input '{elicitation.identifier}' has an invalid '{field}' value.")
        values[field] = cast(str | bool | float | int, value)
    return values


def _default_values(elicitation: SkillElicitation) -> dict[str, str | bool | float | int] | None:
    """Return a form's explicit schema defaults when they satisfy every required field."""
    properties = cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    values: dict[str, str | bool | float | int] = {}
    for field, definition in properties.items():
        if "default" not in definition:
            if field in elicitation.required_fields:
                return None
            continue
        value = definition["default"]
        if not _is_valid_field_value(definition, value):
            return None
        values[field] = cast(str | bool | float | int, value)
    return values


def _defaulted_values(elicitations: tuple[SkillElicitation, ...]) -> ResolvedSkillKeywords | None:
    """Return safe defaults for every unresolved form, or ``None`` when one lacks them."""
    values: dict[str, str | bool | float | int] = {}
    for elicitation in elicitations:
        defaults = _default_values(elicitation)
        if defaults is None:
            return None
        values.update(defaults)
    return ResolvedSkillKeywords(values, defaulted_forms=frozenset(form.identifier for form in elicitations))


def _render_fallback_values(elicitations: tuple[SkillElicitation, ...]) -> ResolvedSkillKeywords | None:
    """Allow forms that explicitly delegate unavailable input to their template."""
    if all(elicitation.fallback == "render" for elicitation in elicitations):
        return ResolvedSkillKeywords({})
    return None


def _response_values(
    elicitations: tuple[SkillElicitation, ...], mcp_context: Context
) -> ResolvedSkillKeywords | Result[Any] | None:
    """Return all accepted modern selections, or ``None`` before the first response."""
    responses = getattr(mcp_context, "input_responses", None)
    if not responses:
        return None
    values: dict[str, str | bool | float | int] = {}
    defaulted_forms: set[str] = set()
    for elicitation in elicitations:
        response = responses.get(elicitation.identifier)
        if response is None:
            return Result.failure(f"Skill input '{elicitation.identifier}' was not completed.")
        if getattr(response, "action", None) == "cancel":
            defaults = _default_values(elicitation)
            if defaults is not None:
                values.update(defaults)
                defaulted_forms.add(elicitation.identifier)
                continue
            if elicitation.fallback == "render":
                continue
            return Result.failure(f"Skill input '{elicitation.identifier}' was not completed.")
        selection = _selection_from_response(elicitation, response)
        if isinstance(selection, Result):
            return selection
        values.update(selection)
    return ResolvedSkillKeywords(values, defaulted_forms=frozenset(defaulted_forms))


def _legacy_model(elicitation: SkillElicitation) -> type[BaseModel]:
    """Build FastMCP's legacy elicitation model from a primitive schema."""
    fields: dict[str, tuple[Any, Any]] = {}
    properties = cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    for name, definition in properties.items():
        annotation: Any = _PRIMITIVE_TYPES[cast(str, definition["type"])]
        default = ... if name in elicitation.required_fields else ""
        fields[name] = (annotation, default)
    return cast(
        type[BaseModel],
        create_model(f"SkillElicitation_{elicitation.identifier.replace('-', '_')}", **cast(Any, fields)),
    )


async def resolve_skill_elicitations(
    frontmatter: Mapping[str, Any], kwargs: Mapping[str, Any], mcp_context: Context | None
) -> ResolvedSkillKeywords | Result[Any] | InputRequiredResult:
    """Collect selected-skill input forms and merge accepted values into template keywords."""
    parsed = parse_skill_elicitations(frontmatter)
    if isinstance(parsed, Result):
        return parsed
    missing = tuple(elicitation for elicitation in parsed if _required_fields_missing(elicitation, kwargs))
    if not missing:
        return ResolvedSkillKeywords(kwargs)
    required = ", ".join(sorted({field for elicitation in missing for field in elicitation.required_fields}))
    if mcp_context is None or not _client_supports_elicitation(mcp_context):
        defaults = _defaulted_values(missing)
        if defaults is not None:
            return ResolvedSkillKeywords({**defaults, **kwargs}, defaulted_forms=defaults.defaulted_forms)
        render_fallback = _render_fallback_values(missing)
        if render_fallback is not None:
            return ResolvedSkillKeywords({**render_fallback, **kwargs})
        return Result.failure(f"This skill requires input; pass: {required}.")

    selections = _response_values(missing, mcp_context)
    if isinstance(selections, Result):
        return selections
    if selections is not None:
        return ResolvedSkillKeywords({**selections, **kwargs}, defaulted_forms=selections.defaulted_forms)
    if getattr(mcp_context.request_context, "protocol_version", None) == "2026-07-28":
        return _input_request(missing)

    values: dict[str, str | bool | float | int] = {}
    defaulted_forms: set[str] = set()
    for elicitation in missing:
        outcome = await mcp_context.elicit(elicitation.message, _legacy_model(elicitation))
        if isinstance(outcome, CancelledElicitation):
            defaults = _default_values(elicitation)
            if defaults is not None:
                values.update(defaults)
                defaulted_forms.add(elicitation.identifier)
                continue
            if elicitation.fallback == "render":
                continue
            return Result.failure(f"Skill input '{elicitation.identifier}' was not completed.")
        if not isinstance(outcome, AcceptedElicitation):
            return Result.failure(f"Skill input '{elicitation.identifier}' was not completed.")
        response = type("AcceptedResponse", (), {"action": "accept", "content": outcome.data.model_dump()})()
        selection = _selection_from_response(elicitation, response)
        if isinstance(selection, Result):
            return selection
        values.update(selection)
    return ResolvedSkillKeywords({**values, **kwargs}, defaulted_forms=frozenset(defaulted_forms))
