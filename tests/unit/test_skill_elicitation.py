"""Behaviour tests for frontmatter-declared skill input forms."""

from types import SimpleNamespace
from typing import cast

import pytest
from fastmcp import Context
from mcp.server.elicitation import CancelledElicitation

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
