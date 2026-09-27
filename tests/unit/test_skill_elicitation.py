"""Behaviour tests for frontmatter-declared skill input forms."""

from types import SimpleNamespace
from typing import cast

import pytest
from fastmcp import Context
from fastmcp.server.elicitation import AcceptedElicitation, CancelledElicitation

from mcp_guide.skill_elicitation import resolve_skill_elicitations


@pytest.mark.anyio
@pytest.mark.parametrize("value", [False, 0])
async def test_explicit_falsey_primitive_satisfies_a_required_skill_form(value: bool | int) -> None:
    """Explicit primitive URI values must not trigger an unnecessary form."""
    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "confirmation": {
                    "message": "Confirm the operation.",
                    "schema": {
                        "type": "object",
                        "properties": {"confirm": {"type": "boolean" if isinstance(value, bool) else "integer"}},
                        "required": ["confirm"],
                    },
                }
            }
        },
        {"confirm": value},
        None,
    )

    assert result == {"confirm": value}


@pytest.mark.anyio
@pytest.mark.parametrize("value", [False, 0])
async def test_accepted_falsey_primitive_satisfies_a_required_skill_form(value: bool | int) -> None:
    """Accepted form values keep valid falsey primitives rather than treating them as missing."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"confirmation": SimpleNamespace(action="accept", content={"confirm": value})},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "confirmation": {
                    "message": "Confirm the operation.",
                    "schema": {
                        "type": "object",
                        "properties": {"confirm": {"type": "boolean" if isinstance(value, bool) else "integer"}},
                        "required": ["confirm"],
                    },
                }
            }
        },
        {},
        cast(Context, context),
    )

    assert result == {"confirm": value}


@pytest.mark.anyio
async def test_cancelled_form_uses_schema_defaults_and_marks_the_defaulted_form() -> None:
    """A client that cancels an optional interaction still receives its safe skill default."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"review-target": SimpleNamespace(action="cancel", content=None)},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "review-target": {
                    "message": "Choose the target for this code review.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["uncommitted", "main"],
                                "default": "uncommitted",
                            }
                        },
                        "required": ["mode"],
                    },
                }
            }
        },
        {},
        cast(Context, context),
    )

    assert result == {"mode": "uncommitted"}
    assert getattr(result, "defaulted_forms") == frozenset({"review-target"})


@pytest.mark.anyio
async def test_unavailable_form_uses_schema_defaults_and_marks_the_defaulted_form() -> None:
    """A non-eliciting caller still receives a safe defaulted skill instruction."""
    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "review-target": {
                    "message": "Choose the target for this code review.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["uncommitted", "main"],
                                "default": "uncommitted",
                            }
                        },
                        "required": ["mode"],
                    },
                }
            }
        },
        {},
        None,
    )

    assert result == {"mode": "uncommitted"}
    assert getattr(result, "defaulted_forms") == frozenset({"review-target"})


@pytest.mark.anyio
async def test_unavailable_form_without_defaults_or_render_fallback_requires_input() -> None:
    """A required form still fails when no declared fallback can resolve it."""
    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "review-target": {
                    "message": "Choose the target for this code review.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string"}},
                        "required": ["mode"],
                    },
                }
            }
        },
        {},
        None,
    )

    assert getattr(result, "success", None) is False
    assert getattr(result, "error", None) == "This skill requires input; pass: mode."


@pytest.mark.anyio
async def test_explicit_uri_keywords_take_precedence_over_schema_defaults() -> None:
    """A fallback form must not replace an explicitly supplied URI keyword."""
    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "review-target": {
                    "message": "Choose the target for this code review.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "default": "uncommitted"},
                            "reference": {"type": "string", "default": "schema-default"},
                        },
                        "required": ["mode"],
                    },
                }
            }
        },
        {"reference": "uri-value"},
        None,
    )

    assert result == {"mode": "uncommitted", "reference": "uri-value"}


@pytest.mark.anyio
async def test_declined_form_does_not_apply_schema_defaults() -> None:
    """An explicit user decline must remain distinct from an unavailable form."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"review-target": SimpleNamespace(action="decline", content=None)},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "review-target": {
                    "message": "Choose the target for this code review.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "default": "uncommitted"}},
                        "required": ["mode"],
                    },
                }
            }
        },
        {},
        cast(Context, context),
    )

    assert getattr(result, "success", None) is False


@pytest.mark.anyio
async def test_legacy_cancelled_form_uses_schema_defaults() -> None:
    """A legacy form cancellation uses the same safe default as a modern cancellation."""

    async def cancel_form(*_args: object) -> CancelledElicitation:
        return CancelledElicitation()

    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2025-11-25"),
        elicit=cancel_form,
    )

    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "review-target": {
                    "message": "Choose the target for this code review.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "default": "uncommitted"}},
                        "required": ["mode"],
                    },
                }
            }
        },
        {},
        cast(Context, context),
    )

    assert result == {"mode": "uncommitted"}
    assert getattr(result, "defaulted_forms") == frozenset({"review-target"})


@pytest.mark.anyio
async def test_modern_cancelled_render_fallback_renders_without_values() -> None:
    """A cancelled optional form permits its declared render fallback."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"optional": SimpleNamespace(action="cancel", content=None)},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "optional": {
                    "message": "Optional.",
                    "fallback": "render",
                    "schema": {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]},
                }
            }
        },
        {},
        cast(Context, context),
    )

    assert result == {}
    assert getattr(result, "defaulted_forms") == frozenset({"optional"})


@pytest.mark.anyio
async def test_legacy_elicitation_rechecks_conditional_forms() -> None:
    """A legacy client is prompted for forms activated by an earlier answer."""
    prompted: list[str] = []

    async def accept_form(_message: str, model: object) -> AcceptedElicitation[object]:
        prompted.append(_message)
        values = {"mode": "branch"} if len(prompted) == 1 else {"branch": "feature/example"}
        return AcceptedElicitation(data=model(**values))  # type: ignore[operator]

    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2025-11-25"),
        elicit=accept_form,
    )
    result = await resolve_skill_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {"type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]},
                },
                "branch": {
                    "message": "Enter branch.",
                    "when": {"mode": "branch"},
                    "schema": {"type": "object", "properties": {"branch": {"type": "string"}}, "required": ["branch"]},
                },
            }
        },
        {},
        cast(Context, context),
    )

    assert prompted == ["Choose target.", "Enter branch."], repr(result)
    assert result == {"mode": "branch", "branch": "feature/example"}
