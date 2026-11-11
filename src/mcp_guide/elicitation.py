"""Frontmatter-declared MCP elicitation for Guide entrypoints."""

import json
import math
import re
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Annotated, Any, ClassVar, Literal, cast

import anyio
from fastmcp import Context
from fastmcp.server.elicitation import AcceptedElicitation, CancelledElicitation, DeclinedElicitation
from mcp_types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult
from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from mcp_guide.core.mcp_log import TRACE_LEVEL, get_logger
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_VALIDATION

logger = get_logger(__name__)

_PRIMITIVE_TYPES: dict[str, type[bool] | type[float] | type[int] | type[str]] = {
    "boolean": bool,
    "integer": int,
    "number": float,
    "string": str,
}
Primitive = str | bool | float | int

_FIELD_SCHEMA_KEYS = ("type", "enum", "description", "default", "minimum", "maximum", "pattern")

_LEGACY_ELICITATION_TIMEOUT_SECONDS = 120.0


def elicitation_timeout_seconds() -> float:
    """Return how long a legacy client may take to answer an input request before it is treated as declined.

    An unanswered request never applies defaults, because nobody chose them.
    """
    return _LEGACY_ELICITATION_TIMEOUT_SECONDS


@dataclass(frozen=True)
class Elicitation:
    """One frontmatter-declared form required before rendering an entrypoint."""

    identifier: str
    message: str
    schema: dict[str, Any]
    fallback: str
    when: Mapping[str, tuple[Primitive, ...]] | None = None

    @property
    def required_fields(self) -> tuple[str, ...]:
        """Return query keywords that satisfy this form when supplied explicitly."""
        return tuple(cast(list[str], self.schema.get("required", [])))


class ResolvedElicitationKeywords(dict[str, Any]):
    """Rendered template keywords, including forms satisfied by safe defaults."""

    def __init__(self, values: Mapping[str, Any], *, defaulted_forms: frozenset[str] = frozenset()) -> None:
        super().__init__(values)
        self.defaulted_forms = defaulted_forms


class ElicitationInterrupted(Exception):
    """Stop a template render to return an elicitation outcome to its entrypoint."""

    def __init__(self, outcome: Result[Any] | InputRequiredResult) -> None:
        self.outcome = outcome
        super().__init__("Template rendering requires elicitation")


@dataclass(frozen=True)
class _ContinuationState:
    """Previously resolved values and forms for one modern interaction."""

    known: Mapping[str, Any]
    defaulted_forms: frozenset[str]
    completed_forms: frozenset[str]
    requested_forms: frozenset[str]


def _failure(message: str) -> Result[Any]:
    """Create a consistent entrypoint-frontmatter validation failure."""
    return Result.failure(f"Invalid elicitation frontmatter: {message}")


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
    if not valid or (enum is not None and value not in enum):
        return False
    pattern = definition.get("pattern")
    if pattern is not None and (not isinstance(value, str) or re.fullmatch(pattern, value) is None):
        return False
    minimum = definition.get("minimum")
    if minimum is not None and cast(float | int, value) < minimum:
        return False
    maximum = definition.get("maximum")
    return maximum is None or cast(float | int, value) <= maximum


def _is_missing_value(values: Mapping[str, Any], field: str) -> bool:
    """Return whether a keyword is absent or cannot satisfy a text field."""
    value = values.get(field)
    return field not in values or value is None or (isinstance(value, str) and not value.strip())


def _validate_schema(identifier: str, value: object) -> Elicitation | Result[Any]:
    """Validate one declarative form without interpreting an entrypoint-specific meaning."""
    if not isinstance(value, Mapping):
        return _failure(f"'{identifier}' must be a mapping")
    message = value.get("message")
    schema = value.get("schema")
    fallback = value.get("fallback", "error")
    raw_when = value.get("when")
    if not isinstance(message, str) or not message.strip():
        return _failure(f"'{identifier}.message' must be a non-empty string")
    if not isinstance(schema, Mapping) or schema.get("type") != "object":
        return _failure(f"'{identifier}.schema' must be an object schema")
    if fallback not in {"error", "render"}:
        return _failure(f"'{identifier}.fallback' must be 'error' or 'render'")
    if raw_when is not None:
        if not isinstance(raw_when, Mapping) or not raw_when:
            return _failure(f"'{identifier}.when' must be a non-empty mapping")
        for field, permitted in raw_when.items():
            values = permitted if isinstance(permitted, list) else [permitted]
            if not isinstance(field, str) or not field or not values or not all(_is_primitive(item) for item in values):
                return _failure(
                    f"'{identifier}.when' must map non-empty field names to primitive values or lists of primitives"
                )
    properties = schema.get("properties")
    required = schema.get("required", [])
    if not isinstance(properties, Mapping) or not properties:
        return _failure(f"'{identifier}.schema.properties' must be a non-empty mapping")
    if not isinstance(required, list) or not all(isinstance(field, str) for field in required):
        return _failure(f"'{identifier}.schema.required' must be a list of field names")
    if not set(required).issubset(properties):
        return _failure(f"'{identifier}.schema.required' must name declared properties")
    normalised_properties: dict[str, dict[str, Any]] = {}
    dropped: dict[str, list[str]] = {}
    for field, definition in properties.items():
        if not isinstance(field, str) or not field or field.startswith("_"):
            return _failure(f"'{identifier}.schema.properties' contains an invalid field name")
        if not isinstance(definition, Mapping) or definition.get("type") not in _PRIMITIVE_TYPES:
            return _failure(f"'{identifier}.schema.properties.{field}' must use a primitive MCP type")
        for constraint in ("minimum", "maximum"):
            if constraint not in definition:
                continue
            if (
                definition["type"] not in {"integer", "number"}
                or not isinstance(definition[constraint], (int, float))
                or isinstance(definition[constraint], bool)
            ):
                return _failure(f"'{identifier}.schema.properties.{field}.{constraint}' must be a numeric constraint")
        pattern = definition.get("pattern")
        if pattern is not None:
            if definition["type"] != "string" or not isinstance(pattern, str) or not pattern:
                return _failure(
                    f"'{identifier}.schema.properties.{field}.pattern' must be a non-empty string constraint"
                )
            try:
                re.compile(pattern)
            except re.error:
                return _failure(f"'{identifier}.schema.properties.{field}.pattern' must be a valid regular expression")
        if "minimum" in definition and "maximum" in definition and definition["minimum"] > definition["maximum"]:
            return _failure(f"'{identifier}.schema.properties.{field}.minimum' must not exceed maximum")
        normalised_definition = {key: value for key, value in definition.items() if key in _FIELD_SCHEMA_KEYS}
        if ignored := sorted(str(key) for key in definition if key not in _FIELD_SCHEMA_KEYS and key != "source"):
            dropped[field] = ignored
        enum = normalised_definition.get("enum")
        if enum is not None and (
            not isinstance(enum, list) or not enum or not all(_is_primitive(item) for item in enum)
        ):
            return _failure(f"'{identifier}.schema.properties.{field}.enum' must contain primitive values")
        if enum is not None:
            normalised_enum = [_normalise_field_value({**normalised_definition, "enum": None}, item) for item in enum]
            if any(item is None for item in normalised_enum):
                return _failure(f"'{identifier}.schema.properties.{field}.enum' must match its field type")
            normalised_definition["enum"] = cast(list[Primitive], normalised_enum)
        if "default" in normalised_definition:
            normalised_default = _normalise_field_value(normalised_definition, normalised_definition["default"])
            if normalised_default is None:
                return _failure(f"'{identifier}.schema.properties.{field}.default' must match its field definition")
            normalised_definition["default"] = normalised_default
        normalised_properties[field] = normalised_definition
    if dropped:
        logger.warning(
            "Elicitation form '%s' ignores unsupported schema keys (not sent to clients): %s",
            identifier,
            "; ".join(f"{field}: {', '.join(keys)}" for field, keys in dropped.items()),
        )
    normalised_schema: dict[str, Any] = {key: schema[key] for key in ("$schema", "type") if key in schema}
    normalised_schema["properties"] = normalised_properties
    if "required" in schema:
        normalised_schema["required"] = list(required)
    when = (
        None
        if raw_when is None
        else {
            cast(str, field): tuple(
                cast(Primitive, item) for item in (permitted if isinstance(permitted, list) else [permitted])
            )
            for field, permitted in cast(Mapping[object, object], raw_when).items()
        }
    )
    return Elicitation(identifier=identifier, message=message, schema=normalised_schema, fallback=fallback, when=when)


def parse_elicitations(frontmatter: Mapping[str, Any]) -> tuple[Elicitation, ...] | Result[Any]:
    """Read generic entrypoint forms from selected frontmatter."""
    raw_elicitations = frontmatter.get("elicitation")
    if raw_elicitations is None:
        return ()
    if not isinstance(raw_elicitations, Mapping):
        return _failure("'elicitation' must be a mapping of form names")

    elicitations: list[Elicitation] = []
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
    field_definitions = {
        field: definition
        for elicitation in elicitations
        for field, definition in cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"]).items()
    }
    normalised: list[Elicitation] = []
    for elicitation in elicitations:
        if elicitation.when is None:
            normalised.append(elicitation)
            continue
        conditions: dict[str, tuple[Primitive, ...]] = {}
        for field, permitted in elicitation.when.items():
            definition = field_definitions.get(field)
            if definition is None:
                return _failure(f"'{elicitation.identifier}.when.{field}' must name a declared form property")
            values = tuple(_normalise_field_value(definition, value) for value in permitted)
            if any(value is None for value in values):
                return _failure(f"'{elicitation.identifier}.when.{field}' must match its declared primitive type")
            conditions[field] = cast(tuple[Primitive, ...], values)
        normalised.append(replace(elicitation, when=conditions))
    field_forms = {
        field: elicitation.identifier
        for elicitation in normalised
        for field in cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    }
    dependencies = {
        elicitation.identifier: {
            field_forms[field] for field in (elicitation.when or {}) if field_forms[field] != elicitation.identifier
        }
        for elicitation in normalised
    }
    if any(
        elicitation.identifier in {field_forms[field] for field in (elicitation.when or {})}
        for elicitation in normalised
    ):
        return _failure("conditional forms must not depend on themselves")

    def visits_cycle(identifier: str, visiting: set[str], visited: set[str]) -> bool:
        if identifier in visiting:
            return True
        if identifier in visited:
            return False
        visiting.add(identifier)
        has_cycle = any(visits_cycle(dependency, visiting, visited) for dependency in dependencies[identifier])
        visiting.remove(identifier)
        visited.add(identifier)
        return has_cycle

    visited: set[str] = set()
    if any(visits_cycle(identifier, set(), visited) for identifier in dependencies):
        return _failure("conditional forms must not have cyclic dependencies")
    return tuple(normalised)


def _normalise_field_value(definition: Mapping[str, Any], value: object) -> Primitive | None:
    """Normalise a URI primitive to its declared schema type."""
    field_type = cast(str, definition["type"])
    try:
        if field_type == "boolean":
            if isinstance(value, bool):
                normalised: Primitive = value
            elif isinstance(value, str) and value.lower() in {"true", "false"}:
                normalised = value.lower() == "true"
            else:
                return None
        elif field_type == "integer":
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                normalised = value
            elif isinstance(value, (str, float)):
                numeric = float(value)
                if not math.isfinite(numeric):
                    return None
                normalised = math.floor(numeric)
            else:
                return None
        elif field_type == "number":
            if isinstance(value, bool):
                return None
            normalised = float(value) if isinstance(value, str | int) else cast(float, value)
            if not isinstance(normalised, float) or not math.isfinite(normalised):
                return None
        else:
            normalised = str(value).lower() if isinstance(value, bool) else value
            if not isinstance(normalised, str):
                return None
    except (OverflowError, TypeError, ValueError):
        return None
    return normalised if _is_valid_field_value(definition, normalised) else None


def _normalise_uri_kwargs(
    elicitations: Sequence[Elicitation], kwargs: Mapping[str, Any]
) -> dict[str, Any] | Result[Any]:
    """Validate and normalise only URI values declared by an elicitation form."""
    definitions = {
        field: definition
        for elicitation in elicitations
        for field, definition in cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"]).items()
    }
    return _normalise_uri_values(definitions, kwargs)


def _normalise_uri_values(
    definitions: Mapping[str, Mapping[str, Any]], kwargs: Mapping[str, Any]
) -> dict[str, Any] | Result[Any]:
    """Validate and normalise URI values against their declared field definitions."""
    normalised = dict(kwargs)
    for field, definition in definitions.items():
        if field not in normalised:
            continue
        if normalised[field] is None or (isinstance(normalised[field], str) and not normalised[field].strip()):
            normalised.pop(field)
            continue
        value = _normalise_field_value(definition, normalised[field])
        if value is None:
            return Result.failure(
                f"Invalid URI keyword '{field}' for its declared input field.", error_type=ERROR_VALIDATION
            )
        normalised[field] = value
    return normalised


def _required_fields_missing(elicitation: Elicitation, kwargs: Mapping[str, Any]) -> bool:
    """Return whether explicit URI keywords leave a required form field unresolved."""
    return any(_is_missing_value(kwargs, field) for field in elicitation.required_fields)


def _condition_state(elicitation: Elicitation, known: Mapping[str, Any]) -> bool | None:
    """Return whether conditions match, do not match, or await a supplied value."""
    if elicitation.when is None:
        return True
    unknown = False
    for field, permitted in elicitation.when.items():
        if _is_missing_value(known, field):
            unknown = True
            continue
        if not any(type(known[field]) is type(value) and known[field] == value for value in permitted):
            return False
    return None if unknown else True


def _pending_forms(
    elicitations: Sequence[Elicitation], values: Mapping[str, Any], completed_forms: set[str]
) -> tuple[Elicitation, ...]:
    """Return currently required forms and suppliers for unresolved conditions."""
    pending = [
        elicitation
        for elicitation in elicitations
        if elicitation.identifier not in completed_forms
        and _condition_state(elicitation, values) is True
        and _required_fields_missing(elicitation, values)
    ]
    unresolved_condition_fields = {
        field
        for elicitation in elicitations
        if _condition_state(elicitation, values) is None
        for field in (elicitation.when or {})
        if _is_missing_value(values, field)
    }
    for elicitation in elicitations:
        properties = cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
        if (
            elicitation.identifier not in completed_forms
            and _condition_state(elicitation, values) is True
            and set(properties).intersection(unresolved_condition_fields)
            and any(_is_missing_value(values, field) for field in properties)
            and elicitation not in pending
        ):
            pending.append(elicitation)
    return tuple(pending)


def _unresolved_input_fields(
    pending: Sequence[Elicitation], elicitations: Sequence[Elicitation], values: Mapping[str, Any]
) -> set[str]:
    """Return required fields plus unresolved condition suppliers for caller guidance."""
    return {
        field
        for elicitation in (*pending, *elicitations)
        for field in (
            *(elicitation.required_fields if elicitation in pending else ()),
            *(elicitation.when or {} if _condition_state(elicitation, values) is None else ()),
        )
        if _is_missing_value(values, field)
    }


def _completed_form_missing_condition_value(
    elicitations: Sequence[Elicitation],
    values: Mapping[str, Any],
    completed_forms: set[str],
    defaulted_forms: set[str],
) -> Result[Any] | None:
    """Reject a completed supplier that left a dependent condition unresolved."""
    suppliers = {
        field: elicitation.identifier
        for elicitation in elicitations
        for field in cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    }
    for elicitation in elicitations:
        if _condition_state(elicitation, values) is not None:
            continue
        for field in elicitation.when or {}:
            supplier = suppliers[field]
            if supplier in completed_forms and supplier not in defaulted_forms and _is_missing_value(values, field):
                return Result.failure(
                    f"Input form '{supplier}' did not provide condition field '{field}' required by "
                    f"'{elicitation.identifier}'.",
                    error_type=ERROR_VALIDATION,
                )
    return None


def _continuation_state(
    entrypoint: str,
    kwargs: Mapping[str, Any],
    args: Sequence[str],
    known: Mapping[str, Any],
    defaulted_forms: set[str],
    completed_forms: set[str],
    requested_forms: Sequence[str],
) -> str | Result[Any]:
    """Encode state that FastMCP seals before sending it to a modern client."""
    try:
        return json.dumps(
            {
                "version": 2,
                "entrypoint": entrypoint,
                "kwargs": dict(kwargs),
                "args": list(args),
                "known": dict(known),
                "defaulted_forms": sorted(defaulted_forms),
                "completed_forms": sorted(completed_forms),
                "requested_forms": sorted(requested_forms),
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError):
        return Result.failure("Elicitation continuation state contains unsupported request values.")


def _restore_continuation_state(
    state: object, entrypoint: str, kwargs: Mapping[str, Any], args: Sequence[str]
) -> _ContinuationState | Result[Any] | None:
    """Restore verified state only for its original entrypoint and URI keywords."""
    if state is None:
        return None
    if not isinstance(state, str):
        return Result.failure("Invalid elicitation continuation state.")
    try:
        payload = json.loads(state)
    except json.JSONDecodeError:
        return Result.failure("Invalid elicitation continuation state.")
    if (
        not isinstance(payload, Mapping)
        or payload.get("version") != 2
        or payload.get("entrypoint") != entrypoint
        or payload.get("kwargs") != dict(kwargs)
        or payload.get("args") != list(args)
        or not isinstance(payload.get("known"), Mapping)
        or not isinstance(payload.get("defaulted_forms"), list)
        or not all(isinstance(form, str) for form in payload["defaulted_forms"])
        or not isinstance(payload.get("completed_forms"), list)
        or not all(isinstance(form, str) for form in payload["completed_forms"])
        or not isinstance(payload.get("requested_forms"), list)
        or not all(isinstance(form, str) for form in payload["requested_forms"])
    ):
        return Result.failure("Elicitation continuation does not match the original request.")
    return _ContinuationState(
        known=dict(cast(Mapping[str, Any], payload["known"])),
        defaulted_forms=frozenset(cast(list[str], payload["defaulted_forms"])),
        completed_forms=frozenset(cast(list[str], payload["completed_forms"])),
        requested_forms=frozenset(cast(list[str], payload["requested_forms"])),
    )


def _input_request(elicitations: tuple[Elicitation, ...], request_state: str) -> InputRequiredResult:
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
        request_state=request_state,
    )


def _client_supports_elicitation(mcp_context: Context) -> bool:
    """Return whether the connected client negotiated MCP elicitation."""
    request_context = getattr(mcp_context, "request_context", None)
    capabilities = getattr(request_context, "capabilities", None)
    if getattr(capabilities, "elicitation", None) is not None:
        return True
    session = getattr(mcp_context, "session", None)
    session_capabilities = getattr(session, "capabilities", None)
    if getattr(session_capabilities, "elicitation", None) is not None:
        return True
    client_params = getattr(session, "client_params", None)
    capabilities = getattr(client_params, "capabilities", None)
    return getattr(capabilities, "elicitation", None) is not None


def _selection_from_content(
    elicitation: Elicitation, content: object
) -> dict[str, str | bool | float | int] | Result[Any]:
    """Validate completed form content against its declared primitive schema."""
    if not isinstance(content, Mapping):
        return Result.failure(f"Input form '{elicitation.identifier}' did not return form values.")

    values: dict[str, str | bool | float | int] = {}
    properties = cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    for field, definition in properties.items():
        value = content.get(field)
        if field in elicitation.required_fields and (
            field not in content or value is None or (isinstance(value, str) and not value.strip())
        ):
            return Result.failure(f"Input form '{elicitation.identifier}' requires '{field}'.")
        if value is None:
            # A skipped optional field holds its declared default on every protocol generation.
            value = definition.get("default")
            if value is None:
                continue
        normalised = _normalise_field_value(definition, value)
        if normalised is None:
            return Result.failure(f"Input form '{elicitation.identifier}' has an invalid '{field}' value.")
        values[field] = normalised
    return values


def _selection_from_response(
    elicitation: Elicitation, response: object
) -> dict[str, str | bool | float | int] | Result[Any]:
    """Validate one accepted modern response through the shared content helper."""
    if getattr(response, "action", None) != "accept":
        return Result.failure(f"Input form '{elicitation.identifier}' was not completed.")
    return _selection_from_content(elicitation, getattr(response, "content", None))


def _default_values(elicitation: Elicitation) -> dict[str, str | bool | float | int] | None:
    """Return a form's explicit schema defaults when they satisfy every required field."""
    properties = cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    values: dict[str, str | bool | float | int] = {}
    for field, definition in properties.items():
        if "default" not in definition:
            if field in elicitation.required_fields:
                return None
            continue
        value = definition["default"]
        normalised = _normalise_field_value(definition, value)
        if normalised is None:
            return None
        values[field] = normalised
    return values or None


def _clean_legacy_schema(schema: dict[str, Any]) -> None:
    """Reduce a generated schema to the keys Guide declares; strict clients (Codex) reject the rest."""
    schema.pop("title", None)
    for definition in schema.get("properties", {}).values():
        definition.pop("title", None)
        if definition.get("default", ...) is None:
            definition.pop("default")
        if "const" in definition:
            # Pydantic renders a one-value Literal as ``const``; clients accept only ``enum``.
            definition["enum"] = [definition.pop("const")]


class _LegacyForm(BaseModel):
    """Base of every legacy form model: strict-client schema cleanup and null-tolerant optional fields."""

    model_config = ConfigDict(json_schema_extra=_clean_legacy_schema)
    optional_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="before")
    @classmethod
    def _drop_null_answers(cls, data: Any) -> Any:
        """Treat ``null`` for an optional property as not answered."""
        if isinstance(data, dict):
            return {name: value for name, value in data.items() if not (value is None and name in cls.optional_fields)}
        return data


def _legacy_model(elicitation: Elicitation) -> type[BaseModel]:
    """Build FastMCP's legacy elicitation model from a primitive schema."""
    fields: dict[str, tuple[Any, Any]] = {}
    properties = cast(Mapping[str, Mapping[str, Any]], elicitation.schema["properties"])
    for name, definition in properties.items():
        annotation: Any = _PRIMITIVE_TYPES[cast(str, definition["type"])]
        if enum := definition.get("enum"):
            annotation = cast(Any, Literal.__getitem__(tuple(cast(list[Primitive], enum))))
        field_kwargs = {
            key: definition[key] for key in ("description", "minimum", "maximum", "pattern") if key in definition
        }
        if "minimum" in field_kwargs:
            field_kwargs["ge"] = field_kwargs.pop("minimum")
        if "maximum" in field_kwargs:
            field_kwargs["le"] = field_kwargs.pop("maximum")
        bounds = {key: definition[key] for key in ("minimum", "maximum") if key in definition}
        if bounds:
            field_kwargs["json_schema_extra"] = bounds
        if field_kwargs:
            annotation = Annotated[annotation, Field(**field_kwargs)]
        default = ... if name in elicitation.required_fields else definition.get("default", None)
        fields[name] = (annotation, default)
    model = create_model(
        f"Elicitation_{elicitation.identifier.replace('-', '_')}",
        __base__=_LegacyForm,
        **cast(Any, fields),
    )
    model.optional_fields = frozenset(name for name in properties if name not in elicitation.required_fields)
    return model


def _shape(values: Mapping[str, Any]) -> dict[str, str]:
    """Describe values by field name and string length (or type) so logs never carry user input."""
    return {
        name: f"str[{len(value)}]" if isinstance(value, str) else type(value).__name__ for name, value in values.items()
    }


def _log_client_capabilities(entrypoint: str, mcp_context: Context | None) -> None:
    """Trace the capability objects behind the negotiated elicitation support."""
    request_context = getattr(mcp_context, "request_context", None)
    session = getattr(mcp_context, "session", None)
    logger.trace(
        "Elicitation %s: request_capabilities=%r session_capabilities=%r client_params_capabilities=%r",
        entrypoint,
        getattr(request_context, "capabilities", None),
        getattr(session, "capabilities", None),
        getattr(getattr(session, "client_params", None), "capabilities", None),
    )


@dataclass
class _Resolution:
    """Mutable state shared by the modern, legacy and no-elicitation resolution paths."""

    entrypoint: str
    forms: tuple[Elicitation, ...]
    uri_keywords: Mapping[str, Any]
    request_keywords: Mapping[str, Any]
    known: dict[str, Any]
    defaulted: set[str]
    completed: set[str]

    def pending(self) -> tuple[Elicitation, ...]:
        """Return the forms that still need input."""
        return _pending_forms(self.forms, self.known, self.completed)

    def incomplete_condition(self) -> Result[Any] | None:
        """Reject a completed supplier that left a dependent condition unresolved."""
        return _completed_form_missing_condition_value(self.forms, self.known, self.completed, self.defaulted)

    def keywords(self) -> ResolvedElicitationKeywords:
        """Return the resolved template keywords."""
        return ResolvedElicitationKeywords(self.known, defaulted_forms=frozenset(self.defaulted))

    def accept(self, elicitation: Elicitation, selection: Mapping[str, Any]) -> None:
        """Record validated values from an answered form; explicit URI keywords always win."""
        self.known.update({key: value for key, value in selection.items() if key not in self.uri_keywords})
        self.completed.add(elicitation.identifier)

    def settle(self, elicitation: Elicitation, outcome: str, *, use_defaults: bool) -> bool:
        """Resolve an unanswered form from its defaults or render fallback; return whether one applied."""
        defaults = _default_values(elicitation) if use_defaults else None
        if defaults is not None:
            self.known.update({key: value for key, value in defaults.items() if key not in self.uri_keywords})
            resolution = "defaults"
        elif elicitation.fallback == "render":
            resolution = "fallback render"
        else:
            return False
        self.defaulted.add(elicitation.identifier)
        self.completed.add(elicitation.identifier)
        logger.debug(
            "Elicitation %s: form %s %s; using %s", self.entrypoint, elicitation.identifier, outcome, resolution
        )
        return True


def _apply_responses(
    state: _Resolution, restored: _ContinuationState | None, responses: Mapping[str, Any], mcp_context: Context | None
) -> Result[Any] | None:
    """Fold a modern client's input responses into the state; return a failure to stop on."""
    logger.debug(
        "Elicitation %s: received responses %s",
        state.entrypoint,
        {name: getattr(response, "action", None) for name, response in responses.items()},
    )
    if logger.isEnabledFor(TRACE_LEVEL):
        for name, response in responses.items():
            content = getattr(response, "content", None)
            logger.trace(
                "Elicitation %s: response %s content=%s",
                state.entrypoint,
                name,
                _shape(content) if isinstance(content, Mapping) else None,
            )
    modern = getattr(getattr(mcp_context, "request_context", None), "protocol_version", None) == "2026-07-28"
    if restored is None and hasattr(mcp_context, "request_state") and modern:
        return Result.failure("Elicitation response does not match the original request.")
    if restored is not None and not set(responses).issubset(restored.requested_forms):
        return Result.failure("Elicitation response does not match the original request.")
    for elicitation in state.forms:
        response = responses.get(elicitation.identifier)
        if response is None:
            continue
        action = getattr(response, "action", None)
        if action in _UNANSWERED_ACTIONS and state.settle(
            elicitation, _UNANSWERED_ACTIONS[action], use_defaults=action == "cancel"
        ):
            continue
        selection = _selection_from_response(elicitation, response)
        if isinstance(selection, Result):
            logger.debug(
                "Elicitation %s: form %s response %s rejected: %s",
                state.entrypoint,
                elicitation.identifier,
                action,
                selection.error,
            )
            return selection
        state.accept(elicitation, selection)
    return None


_UNANSWERED_ACTIONS = {"cancel": "cancelled", "decline": "declined"}


def _resolve_without_elicitation(
    state: _Resolution, missing: tuple[Elicitation, ...]
) -> ResolvedElicitationKeywords | Result[Any]:
    """Resolve forms from defaults or render fallbacks when the client cannot elicit."""
    logger.debug("Elicitation %s: client cannot elicit; forms %s", state.entrypoint, [e.identifier for e in missing])
    while True:
        settled = [state.settle(elicitation, "unsupported", use_defaults=True) for elicitation in missing]
        incomplete_condition = state.incomplete_condition()
        if incomplete_condition is not None:
            return incomplete_condition
        missing = state.pending()
        if not missing:
            return state.keywords()
        if not any(settled):
            required = ", ".join(sorted(_unresolved_input_fields(missing, state.forms, state.known)))
            return Result.failure(f"This entrypoint requires input; pass URI keywords: {required}.")


def _request_modern(
    state: _Resolution, missing: tuple[Elicitation, ...], args: Sequence[str]
) -> InputRequiredResult | Result[Any]:
    """Return one input_required result for every missing form."""
    request_state = _continuation_state(
        state.entrypoint,
        state.request_keywords,
        args,
        state.known,
        state.defaulted,
        state.completed,
        [elicitation.identifier for elicitation in missing],
    )
    if isinstance(request_state, Result):
        return request_state
    logger.debug(
        "Elicitation %s: returning input_required for forms %s", state.entrypoint, [e.identifier for e in missing]
    )
    for elicitation in missing:
        logger.trace(
            "Elicitation %s: input request %s schema=%r", state.entrypoint, elicitation.identifier, elicitation.schema
        )
    return _input_request(missing, request_state)


async def _ask_legacy(
    mcp_context: Context, entrypoint: str, elicitation: Elicitation
) -> AcceptedElicitation[Any] | DeclinedElicitation | CancelledElicitation | None:
    """Ask a legacy client one form; return None when it does not answer in time."""
    model = _legacy_model(elicitation)
    logger.trace(
        "Elicitation %s: legacy request %s schema=%r", entrypoint, elicitation.identifier, model.model_json_schema()
    )
    try:
        with anyio.fail_after(elicitation_timeout_seconds()):
            return await mcp_context.elicit(elicitation.message, model)
    except TimeoutError:
        return None


async def _elicit_legacy(
    state: _Resolution, mcp_context: Context, missing: tuple[Elicitation, ...]
) -> ResolvedElicitationKeywords | Result[Any]:
    """Ask a legacy client for each missing form in turn, rechecking conditions after every answer."""
    logger.debug(
        "Elicitation %s: requesting forms %s sequentially (legacy)", state.entrypoint, [e.identifier for e in missing]
    )
    pending = list(missing)
    while pending:
        elicitation = pending.pop(0)
        outcome = await _ask_legacy(mcp_context, state.entrypoint, elicitation)
        if isinstance(outcome, AcceptedElicitation):
            selection = _selection_from_content(elicitation, outcome.data.model_dump())
            if isinstance(selection, Result):
                return selection
            state.accept(elicitation, selection)
            incomplete_condition = state.incomplete_condition()
            if incomplete_condition is not None:
                return incomplete_condition
        else:
            if outcome is None:
                settled = state.settle(elicitation, "unanswered", use_defaults=False)
            elif isinstance(outcome, CancelledElicitation):
                settled = state.settle(elicitation, "cancelled", use_defaults=True)
            elif isinstance(outcome, DeclinedElicitation):
                settled = state.settle(elicitation, "declined", use_defaults=False)
            else:
                settled = False
            if not settled:
                return Result.failure(f"Input form '{elicitation.identifier}' was not completed.")
        pending = list(state.pending())
    return state.keywords()


async def resolve_elicitations(
    frontmatter: Mapping[str, Any],
    kwargs: Mapping[str, Any],
    mcp_context: Context | None,
    *,
    entrypoint: str = "entrypoint",
    args: Sequence[str] = (),
) -> ResolvedElicitationKeywords | Result[Any] | InputRequiredResult:
    """Collect entrypoint input forms and merge accepted values into template keywords."""
    parsed = parse_elicitations(frontmatter)
    if isinstance(parsed, Result):
        return parsed
    normalised_kwargs = _normalise_uri_kwargs(parsed, kwargs)
    if isinstance(normalised_kwargs, Result):
        logger.debug("Elicitation %s: URI keyword validation failed: %s", entrypoint, normalised_kwargs.error)
        return normalised_kwargs
    can_elicit = mcp_context is not None and _client_supports_elicitation(mcp_context)
    protocol = getattr(getattr(mcp_context, "request_context", None), "protocol_version", None)
    logger.debug(
        "Elicitation %s: protocol=%s elicitation=%s forms=%s uri_keywords=%s",
        entrypoint,
        protocol,
        can_elicit,
        [elicitation.identifier for elicitation in parsed],
        sorted(normalised_kwargs),
    )
    _log_client_capabilities(entrypoint, mcp_context)
    restored = _restore_continuation_state(
        getattr(mcp_context, "request_state", None) if mcp_context is not None else None,
        entrypoint,
        normalised_kwargs,
        args,
    )
    if isinstance(restored, Result):
        logger.debug("Elicitation %s: continuation state rejected: %s", entrypoint, restored.error)
        return restored
    state = _Resolution(
        entrypoint=entrypoint,
        forms=parsed,
        uri_keywords=normalised_kwargs,
        request_keywords=kwargs,
        known=dict(restored.known if restored is not None else normalised_kwargs),
        defaulted=set(restored.defaulted_forms if restored is not None else ()),
        completed=set(restored.completed_forms if restored is not None else ()),
    )
    responses = getattr(mcp_context, "input_responses", None) if mcp_context is not None else None
    if responses:
        failure = _apply_responses(state, restored, responses, mcp_context)
        if failure is not None:
            return failure
    incomplete_condition = state.incomplete_condition()
    if incomplete_condition is not None:
        return incomplete_condition
    missing = state.pending()
    if logger.isEnabledFor(TRACE_LEVEL):
        logger.trace("Elicitation %s: known values=%s", entrypoint, _shape(state.known))
    if not missing:
        return state.keywords()
    if mcp_context is None or not can_elicit:
        return _resolve_without_elicitation(state, missing)
    if protocol == "2026-07-28":
        return _request_modern(state, missing, args)
    return await _elicit_legacy(state, mcp_context, missing)


async def _resolve_rendered_form(
    elicitation: Elicitation,
    *,
    uri_keywords: Mapping[str, Any],
    request_keywords: Mapping[str, Any],
    known: Mapping[str, Any],
    mcp_context: Context | None,
    entrypoint: str,
    args: Sequence[str],
    restore_continuation: bool,
    defaulted_forms: set[str],
    completed_forms: set[str],
) -> ResolvedElicitationKeywords | Result[Any] | InputRequiredResult:
    """Resolve the one form reached by the active Mustache render.

    It intentionally never discovers another form. A conditional template
    branch therefore controls whether its form is requested at all.
    """
    normalised_keywords = _normalise_uri_kwargs((elicitation,), uri_keywords)
    if isinstance(normalised_keywords, Result):
        return normalised_keywords
    restored = (
        _restore_continuation_state(
            getattr(mcp_context, "request_state", None) if mcp_context is not None else None,
            entrypoint,
            request_keywords,
            args,
        )
        if restore_continuation
        else None
    )
    if isinstance(restored, Result):
        return restored
    state = _Resolution(
        entrypoint=entrypoint,
        forms=(elicitation,),
        uri_keywords=normalised_keywords,
        request_keywords=request_keywords,
        known=dict(restored.known if restored is not None else known),
        defaulted=set(restored.defaulted_forms if restored is not None else defaulted_forms),
        completed=set(restored.completed_forms if restored is not None else completed_forms),
    )
    responses = (
        getattr(mcp_context, "input_responses", None) if restore_continuation and mcp_context is not None else None
    )
    if responses:
        failure = _apply_responses(state, restored, responses, mcp_context)
        if failure is not None:
            return failure

    condition = _condition_state(elicitation, state.known)
    if condition is None:
        missing = ", ".join(
            sorted(field for field in (elicitation.when or {}) if _is_missing_value(state.known, field))
        )
        return Result.failure(
            f"Input form '{elicitation.identifier}' requires values from an earlier rendered form: {missing}.",
            error_type=ERROR_VALIDATION,
        )
    if (
        condition is False
        or elicitation.identifier in state.completed
        or not _required_fields_missing(elicitation, state.known)
    ):
        return state.keywords()

    can_elicit = mcp_context is not None and _client_supports_elicitation(mcp_context)
    protocol = getattr(getattr(mcp_context, "request_context", None), "protocol_version", None)
    if not can_elicit:
        return _resolve_without_elicitation(state, (elicitation,))
    if protocol == "2026-07-28":
        return _request_modern(state, (elicitation,), args)
    assert mcp_context is not None
    return await _elicit_legacy(state, mcp_context, (elicitation,))


@dataclass
class ElicitationRuntime:
    """Request-local forms and values for one rendered command or skill."""

    kwargs: dict[str, Any]
    original_uri_kwargs: dict[str, Any]
    mcp_context: Context | None
    entrypoint: str
    args: Sequence[str] = ()
    forms: dict[str, Elicitation] = field(default_factory=dict)
    omitted_forms: set[str] = field(default_factory=set)
    fields: dict[str, Mapping[str, Any]] = field(default_factory=dict)
    pending_declarations: list[tuple[object, Mapping[str, Any] | None]] = field(default_factory=list)
    defaulted_forms: set[str] = field(default_factory=set)
    completed_forms: set[str] = field(default_factory=set)
    continuation_prepared: bool = False
    continuation_consumed: bool = False

    def register_forms(self, raw_forms: object, context: Mapping[str, Any] | None = None) -> None:
        """Register a rendered declaration for lazy validation at its first elicit section."""
        if raw_forms is not None:
            self.pending_declarations.append((raw_forms, context))

    def _update_registered_forms(self) -> Result[Any] | None:
        """Validate declarations only when a rendered elicit section needs them."""
        while self.pending_declarations:
            raw_forms, context = self.pending_declarations.pop(0)
            update_error = self.update_forms(raw_forms, context)
            if update_error is not None:
                return update_error
        return None

    def prepare_continuation(self) -> Result[Any] | None:
        """Restore sealed request state before the template chooses its next section."""
        if self.continuation_prepared:
            return None
        self.continuation_prepared = True
        restored = _restore_continuation_state(
            getattr(self.mcp_context, "request_state", None) if self.mcp_context is not None else None,
            self.entrypoint,
            self.original_uri_kwargs,
            self.args,
        )
        if isinstance(restored, Result):
            return restored
        if restored is not None:
            self.kwargs.update(restored.known)
            self.defaulted_forms.update(restored.defaulted_forms)
            self.completed_forms.update(restored.completed_forms)
        return None

    def update_forms(self, raw_forms: object, context: Mapping[str, Any] | None = None) -> Result[Any] | None:
        """Register forms from a template whose body is now eligible to render."""
        if raw_forms is None:
            return None
        if not isinstance(raw_forms, Mapping):
            return _failure("'elicitation' must be a mapping of form names")
        from mcp_guide.input_sources import prepare_form_sources

        prepared = prepare_form_sources(raw_forms, context, self.args, self.kwargs)
        omitted_identifiers = {
            identifier for identifier in raw_forms if isinstance(identifier, str) and identifier not in prepared
        }
        removed_fields: set[str] = set()
        for identifier in omitted_identifiers:
            previous = self.forms.pop(identifier, None)
            if previous is not None:
                removed_fields.update(cast(Mapping[str, Mapping[str, Any]], previous.schema["properties"]))
            self.defaulted_forms.discard(identifier)
            self.completed_forms.discard(identifier)
        self.omitted_forms.update(omitted_identifiers)
        for identifier, definition in prepared.items():
            if not isinstance(identifier, str) or not identifier:
                return _failure("form names must be non-empty strings")
            parsed = _validate_schema(identifier, definition)
            if isinstance(parsed, Result):
                return parsed
            self.omitted_forms.discard(identifier)
            previous = self.forms.get(identifier)
            if previous is not None and previous.schema != parsed.schema:
                previous_fields = cast(Mapping[str, Mapping[str, Any]], previous.schema["properties"])
                replacement_fields = cast(Mapping[str, Mapping[str, Any]], parsed.schema["properties"])
                for field, previous_definition in previous_fields.items():
                    if replacement_fields.get(field) == previous_definition:
                        continue
                    if field not in self.original_uri_kwargs:
                        self.kwargs.pop(field, None)
                self.defaulted_forms.discard(identifier)
                self.completed_forms.discard(identifier)
            self.forms[identifier] = parsed
        self.fields = {
            field: definition
            for declared in self.forms.values()
            for field, definition in cast(Mapping[str, Mapping[str, Any]], declared.schema["properties"]).items()
        }
        for field in removed_fields - self.fields.keys() - self.original_uri_kwargs.keys():
            self.kwargs.pop(field, None)
        for elicitation in self.forms.values():
            if elicitation.when is None:
                continue
            normalised: dict[str, tuple[Primitive, ...]] = {}
            for field, permitted in elicitation.when.items():
                definition = self.fields.get(field)
                if definition is None:
                    return _failure(f"'{elicitation.identifier}.when.{field}' must name a declared form property")
                values = tuple(_normalise_field_value(definition, value) for value in permitted)
                if any(value is None for value in values):
                    return _failure(f"'{elicitation.identifier}.when.{field}' must match its declared primitive type")
                normalised[field] = cast(tuple[Primitive, ...], values)
            self.forms[elicitation.identifier] = replace(elicitation, when=normalised)
        normalised_uri = _normalise_uri_values(self.fields, self.original_uri_kwargs)
        if isinstance(normalised_uri, Result):
            return normalised_uri
        self.kwargs.update(normalised_uri)
        return None

    def lambda_for(self, identifier: str) -> Callable[..., Awaitable[str]]:
        """Return the Chevron compat lambda for one syntactically referenced form."""
        import chevron

        @chevron.compat
        async def invoke(body: str, render: Callable[[str, Mapping[str, Any]], Awaitable[str]]) -> str:
            update_error = self._update_registered_forms()
            if update_error is not None:
                raise ElicitationInterrupted(update_error)
            elicitation = self.forms.get(identifier)
            if elicitation is None:
                if identifier in self.omitted_forms:
                    return await render(body, {"kwargs": self.kwargs})
                raise ElicitationInterrupted(
                    Result.failure(
                        f"Template references undeclared input form '{identifier}'.", error_type=ERROR_VALIDATION
                    )
                )
            responses = getattr(self.mcp_context, "input_responses", None) if self.mcp_context is not None else None
            has_response = isinstance(responses, Mapping) and identifier in responses
            resolved = await _resolve_rendered_form(
                elicitation,
                uri_keywords=self.original_uri_kwargs,
                request_keywords=self.original_uri_kwargs,
                known=self.kwargs,
                mcp_context=self.mcp_context,
                entrypoint=self.entrypoint,
                args=self.args,
                restore_continuation=not self.continuation_consumed and has_response,
                defaulted_forms=self.defaulted_forms,
                completed_forms=self.completed_forms,
            )
            if isinstance(resolved, (Result, InputRequiredResult)):
                raise ElicitationInterrupted(resolved)
            self.kwargs.update(resolved)
            self.defaulted_forms.update(resolved.defaulted_forms)
            self.completed_forms.add(identifier)
            self.continuation_consumed = self.continuation_consumed or has_response
            return await render(
                body,
                {
                    "kwargs": self.kwargs,
                    "elicitation": {"defaulted_forms": {name: True for name in self.defaulted_forms}},
                },
            )

        return invoke
