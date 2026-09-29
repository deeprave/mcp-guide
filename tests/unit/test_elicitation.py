"""Behaviour tests for frontmatter-declared skill input forms."""

from types import SimpleNamespace
from typing import cast

import pytest
from fastmcp import Context
from fastmcp.server.elicitation import AcceptedElicitation, CancelledElicitation
from mcp_types import InputRequiredResult

from mcp_guide.elicitation import _legacy_model, parse_elicitations, resolve_elicitations


@pytest.fixture
def modern_elicitation_context():
    """Build isolated modern-MCP contexts for resolver behaviour tests."""
    session = SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={})))
    request_context = SimpleNamespace(protocol_version="2026-07-28")

    def build(*, input_responses=None, request_state=...):
        values = {
            "session": session,
            "input_responses": input_responses,
            "request_context": request_context,
        }
        if request_state is not ...:
            values["request_state"] = request_state
        return cast(Context, SimpleNamespace(**values))

    return build


@pytest.mark.anyio
@pytest.mark.parametrize("value", [False, 0])
async def test_explicit_falsey_primitive_satisfies_a_required_skill_form(value: bool | int) -> None:
    """Explicit primitive URI values must not trigger an unnecessary form."""
    result = await resolve_elicitations(
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
async def test_numeric_constraints_reject_out_of_range_uri_values() -> None:
    """Declared numeric limits apply to URI values before an entrypoint renders."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "options": {
                    "message": "Choose attempts.",
                    "schema": {
                        "type": "object",
                        "properties": {"attempts": {"type": "integer", "minimum": 1}},
                        "required": ["attempts"],
                    },
                }
            }
        },
        {"attempts": "0"},
        None,
    )

    assert getattr(result, "error_type", None) == "validation_error"


@pytest.mark.anyio
async def test_integer_uri_values_floor_before_enum_and_bounds_validation() -> None:
    """Finite numeric integer input has one floor-based representation everywhere."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "options": {
                    "message": "Choose attempts.",
                    "schema": {
                        "type": "object",
                        "properties": {"attempts": {"type": "integer", "enum": [2.9], "minimum": 2}},
                        "required": ["attempts"],
                    },
                }
            }
        },
        {"attempts": "2.9"},
        None,
    )

    assert result == {"attempts": 2}


def test_legacy_model_preserves_enum_bounds_and_help_metadata() -> None:
    """Legacy elicitation exposes the same primitive constraints as modern clients."""
    parsed = parse_elicitations(
        {
            "elicitation": {
                "options": {
                    "message": "Choose.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "attempts": {
                                "type": "integer",
                                "enum": [2, 3],
                                "minimum": 2,
                                "maximum": 3,
                                "description": "Number of attempts.",
                            }
                        },
                        "required": ["attempts"],
                    },
                }
            }
        }
    )

    assert isinstance(parsed, tuple)
    model = _legacy_model(parsed[0])
    schema = model.model_json_schema()
    assert schema["properties"]["attempts"]["enum"] == [2, 3]
    assert schema["properties"]["attempts"]["minimum"] == 2
    assert schema["properties"]["attempts"]["maximum"] == 3
    assert schema["properties"]["attempts"]["description"] == "Number of attempts."
    with pytest.raises(Exception):
        model(attempts=4)


@pytest.mark.anyio
async def test_overflowing_numeric_uri_value_is_a_validation_failure() -> None:
    """An unrepresentable numeric URI value must not escape as an exception."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "options": {
                    "message": "Choose threshold.",
                    "schema": {
                        "type": "object",
                        "properties": {"threshold": {"type": "number"}},
                        "required": ["threshold"],
                    },
                }
            }
        },
        {"threshold": "1e1000000"},
        None,
    )

    assert getattr(result, "error_type", None) == "validation_error"


@pytest.mark.anyio
@pytest.mark.parametrize("value", [False, 0])
async def test_accepted_falsey_primitive_satisfies_a_required_skill_form(
    value: bool | int, modern_elicitation_context
) -> None:
    """Accepted form values keep valid falsey primitives rather than treating them as missing."""
    context = modern_elicitation_context(
        input_responses={"confirmation": SimpleNamespace(action="accept", content={"confirm": value})}
    )

    result = await resolve_elicitations(
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
        context,
    )

    assert result == {"confirm": value}


@pytest.mark.anyio
async def test_cancelled_form_uses_schema_defaults_and_marks_the_defaulted_form(modern_elicitation_context) -> None:
    """A client that cancels an optional interaction still receives its safe skill default."""
    context = modern_elicitation_context(
        input_responses={"review-target": SimpleNamespace(action="cancel", content=None)}
    )

    result = await resolve_elicitations(
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
        context,
    )

    assert result == {"mode": "uncommitted"}
    assert getattr(result, "defaulted_forms") == frozenset({"review-target"})


@pytest.mark.anyio
async def test_unavailable_form_uses_schema_defaults_and_marks_the_defaulted_form() -> None:
    """A non-eliciting caller still receives a safe defaulted skill instruction."""
    result = await resolve_elicitations(
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
    result = await resolve_elicitations(
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
    assert getattr(result, "error", None) == "This entrypoint requires input; pass URI keywords: mode."


@pytest.mark.anyio
async def test_modern_protocol_requests_input_without_client_information() -> None:
    """Modern request capability is sufficient when optional client metadata is absent."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "choice": {
                    "message": "Choose.",
                    "schema": {"type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]},
                }
            }
        },
        {},
        cast(
            Context,
            SimpleNamespace(
                request_context=SimpleNamespace(
                    protocol_version="2026-07-28", capabilities=SimpleNamespace(elicitation={})
                )
            ),
        ),
    )

    assert isinstance(result, InputRequiredResult)


@pytest.mark.anyio
async def test_explicit_uri_keywords_take_precedence_over_schema_defaults() -> None:
    """A fallback form must not replace an explicitly supplied URI keyword."""
    result = await resolve_elicitations(
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
async def test_completed_optional_supplier_cannot_silently_skip_a_dependent_form(modern_elicitation_context) -> None:
    """An accepted supplier must provide every condition value its dependants need."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {"type": "object", "properties": {"mode": {"type": "string"}}},
                },
                "detail": {
                    "message": "Choose detail.",
                    "when": {"mode": "branch"},
                    "schema": {
                        "type": "object",
                        "properties": {"reference": {"type": "string"}},
                        "required": ["reference"],
                    },
                },
            }
        },
        {},
        modern_elicitation_context(input_responses={"target": SimpleNamespace(action="accept", content={})}),
    )

    assert getattr(result, "error_type", None) == "validation_error"
    assert "condition field 'mode'" in getattr(result, "error", "")


@pytest.mark.anyio
async def test_blank_uri_keyword_allows_a_schema_default() -> None:
    """An empty declared URI value is absent rather than a default-blocking value."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "review-target": {
                    "message": "Choose target.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "default": "uncommitted"}},
                        "required": ["mode"],
                    },
                }
            }
        },
        {"mode": "  "},
        None,
    )

    assert result == {"mode": "uncommitted"}


@pytest.mark.anyio
async def test_non_eliciting_client_resolves_mixed_default_and_render_fallback_forms() -> None:
    """Each unavailable form resolves independently before reporting a real input requirement."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "default": "uncommitted"}},
                        "required": ["mode"],
                    },
                },
                "detail": {
                    "message": "Choose detail.",
                    "fallback": "render",
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string"}},
                        "required": ["detail"],
                    },
                },
            }
        },
        {},
        None,
    )

    assert result == {"mode": "uncommitted"}
    assert getattr(result, "defaulted_forms") == frozenset({"target", "detail"})


def test_undeclared_when_field_is_a_frontmatter_error() -> None:
    """Conditional forms can only depend on an effective declared property."""
    result = parse_elicitations(
        {
            "elicitation": {
                "detail": {
                    "message": "Choose detail.",
                    "when": {"missing": "value"},
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string"}},
                        "required": ["detail"],
                    },
                }
            }
        }
    )

    assert getattr(result, "success", None) is False


def test_enum_members_must_match_the_declared_primitive_type() -> None:
    """Impossible enum declarations fail before they can request user input."""
    result = parse_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose a target.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "enum": [1]}},
                        "required": ["mode"],
                    },
                }
            }
        }
    )

    assert getattr(result, "success", None) is False


@pytest.mark.anyio
async def test_declined_form_does_not_apply_schema_defaults() -> None:
    """An explicit user decline must remain distinct from an unavailable form."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"review-target": SimpleNamespace(action="decline", content=None)},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await resolve_elicitations(
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

    result = await resolve_elicitations(
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

    result = await resolve_elicitations(
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
    result = await resolve_elicitations(
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


@pytest.mark.anyio
async def test_legacy_cancellation_rechecks_forms_activated_by_defaults() -> None:
    """A legacy cancellation must reconsider branches activated by its defaults."""
    prompted: list[str] = []

    async def respond(_message: str, model: object) -> AcceptedElicitation[object] | CancelledElicitation:
        prompted.append(_message)
        if len(prompted) == 1:
            return CancelledElicitation()
        return AcceptedElicitation(data=model(reference="main"))  # type: ignore[operator]

    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2025-11-25"),
        elicit=respond,
    )
    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "default": "branch"}},
                        "required": ["mode"],
                    },
                },
                "reference": {
                    "message": "Enter reference.",
                    "when": {"mode": "branch"},
                    "schema": {
                        "type": "object",
                        "properties": {"reference": {"type": "string"}},
                        "required": ["reference"],
                    },
                },
            }
        },
        {},
        cast(Context, context),
    )

    assert prompted == ["Choose target.", "Enter reference."]
    assert result == {"mode": "branch", "reference": "main"}


@pytest.mark.anyio
async def test_modern_response_requires_a_continuation_state() -> None:
    """A modern response cannot be accepted outside its sealed input request."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"choice": SimpleNamespace(action="accept", content={"count": 1})},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
        request_state=None,
    )

    result = await resolve_elicitations(
        {
            "elicitation": {
                "choice": {
                    "message": "Choose count.",
                    "schema": {
                        "type": "object",
                        "properties": {"count": {"type": "number"}},
                        "required": ["count"],
                    },
                }
            }
        },
        {},
        cast(Context, context),
    )

    assert result.success is False


@pytest.mark.anyio
async def test_number_response_is_normalised_before_conditional_matching() -> None:
    """Accepted numeric values use the schema's float representation for branches."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"choice": SimpleNamespace(action="accept", content={"count": 1})},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await resolve_elicitations(
        {
            "elicitation": {
                "choice": {
                    "message": "Choose count.",
                    "schema": {
                        "type": "object",
                        "properties": {"count": {"type": "number"}},
                        "required": ["count"],
                    },
                },
                "detail": {
                    "message": "Choose detail.",
                    "when": {"count": 1.0},
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string", "default": "on"}},
                        "required": ["detail"],
                    },
                },
            }
        },
        {},
        cast(Context, context),
    )

    assert isinstance(result, InputRequiredResult)
    assert set(result.input_requests) == {"detail"}
    completed = await resolve_elicitations(
        {
            "elicitation": {
                "choice": {
                    "message": "Choose count.",
                    "schema": {
                        "type": "object",
                        "properties": {"count": {"type": "number"}},
                        "required": ["count"],
                    },
                },
                "detail": {
                    "message": "Choose detail.",
                    "when": {"count": 1.0},
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string", "default": "on"}},
                        "required": ["detail"],
                    },
                },
            }
        },
        {},
        cast(
            Context,
            SimpleNamespace(
                session=context.session,
                request_context=context.request_context,
                request_state=result.request_state,
                input_responses={"detail": SimpleNamespace(action="accept", content={"detail": "extra"})},
            ),
        ),
    )

    assert completed == {"count": 1.0, "detail": "extra"}


@pytest.mark.anyio
async def test_modern_elicitation_requests_only_a_multi_condition_branch() -> None:
    """A branch becomes applicable only when every accepted or URI condition matches."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string"}, "scope": {"type": "string"}},
                        "required": ["mode", "scope"],
                    },
                },
                "reference": {
                    "message": "Enter reference.",
                    "when": {"mode": ["branch", "pull-request"], "scope": "remote"},
                    "schema": {
                        "type": "object",
                        "properties": {"reference": {"type": "string"}},
                        "required": ["reference"],
                    },
                },
            }
        },
        {"mode": "branch", "scope": "remote"},
        cast(Context, context),
    )

    assert isinstance(result, InputRequiredResult)
    assert set(result.input_requests) == {"reference"}


@pytest.mark.anyio
async def test_multi_condition_branch_is_skipped_when_one_known_value_does_not_match() -> None:
    """A known non-matching condition skips its form without requesting input."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string"}, "scope": {"type": "string"}},
                        "required": ["mode", "scope"],
                    },
                },
                "reference": {
                    "message": "Enter reference.",
                    "when": {"mode": ["branch", "pull-request"], "scope": "remote"},
                    "schema": {
                        "type": "object",
                        "properties": {"reference": {"type": "string"}},
                        "required": ["reference"],
                    },
                },
            }
        },
        {"mode": "main", "scope": "remote"},
        None,
    )

    assert result == {"mode": "main", "scope": "remote"}


@pytest.mark.anyio
async def test_modern_continuation_retains_accepted_values_for_a_follow_up_form() -> None:
    """A verified retry retains an earlier answer while it requests a conditional form."""
    frontmatter = {
        "elicitation": {
            "target": {
                "message": "Choose target.",
                "schema": {"type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]},
            },
            "reference": {
                "message": "Enter reference.",
                "when": {"mode": "branch"},
                "schema": {
                    "type": "object",
                    "properties": {"reference": {"type": "string"}},
                    "required": ["reference"],
                },
            },
        }
    }
    base = dict(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )
    initial = await resolve_elicitations(
        frontmatter, {}, cast(Context, SimpleNamespace(**base)), entrypoint="skill:review"
    )

    assert isinstance(initial, InputRequiredResult)
    assert set(initial.input_requests) == {"target"}
    accepted_target = await resolve_elicitations(
        frontmatter,
        {},
        cast(
            Context,
            SimpleNamespace(
                **base,
                request_state=initial.request_state,
                input_responses={"target": SimpleNamespace(action="accept", content={"mode": "branch"})},
            ),
        ),
        entrypoint="skill:review",
    )

    assert isinstance(accepted_target, InputRequiredResult)
    assert set(accepted_target.input_requests) == {"reference"}
    completed = await resolve_elicitations(
        frontmatter,
        {},
        cast(
            Context,
            SimpleNamespace(
                **base,
                request_state=accepted_target.request_state,
                input_responses={
                    "reference": SimpleNamespace(action="accept", content={"reference": "feature/example"})
                },
            ),
        ),
        entrypoint="skill:review",
    )

    assert completed == {"mode": "branch", "reference": "feature/example"}


@pytest.mark.anyio
async def test_optional_condition_supplier_is_requested_before_its_dependent_form(modern_elicitation_context) -> None:
    """An optional supplier still needs elicitation when a branch depends on it."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {"type": "object", "properties": {"mode": {"type": "string"}}},
                },
                "reference": {
                    "message": "Enter reference.",
                    "when": {"mode": "branch"},
                    "schema": {
                        "type": "object",
                        "properties": {"reference": {"type": "string"}},
                        "required": ["reference"],
                    },
                },
            }
        },
        {},
        modern_elicitation_context(),
    )

    assert isinstance(result, InputRequiredResult)
    assert set(result.input_requests) == {"target"}


@pytest.mark.anyio
async def test_modern_continuation_rejects_changed_command_positional_arguments() -> None:
    """A command retry must retain the positional target selected initially."""
    frontmatter = {
        "elicitation": {
            "choice": {
                "message": "Choose.",
                "schema": {"type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]},
            }
        }
    }
    base = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )
    pending = await resolve_elicitations(
        frontmatter, {}, cast(Context, base), entrypoint="command:review", args=["one"]
    )

    result = await resolve_elicitations(
        frontmatter,
        {},
        cast(
            Context,
            SimpleNamespace(
                session=base.session,
                request_context=base.request_context,
                request_state=pending.request_state,
                input_responses={"choice": SimpleNamespace(action="accept", content={"mode": "summary"})},
            ),
        ),
        entrypoint="command:review",
        args=["two"],
    )

    assert result.success is False


@pytest.mark.anyio
async def test_modern_continuation_rejects_an_unsolicited_form_response() -> None:
    """A retry cannot add values for a form that was not requested."""
    frontmatter = {
        "elicitation": {
            "choice": {
                "message": "Choose.",
                "schema": {"type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]},
            },
            "other": {
                "message": "Other.",
                "when": {"mode": "other"},
                "schema": {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]},
            },
        }
    }
    base = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )
    pending = await resolve_elicitations(frontmatter, {}, cast(Context, base))

    result = await resolve_elicitations(
        frontmatter,
        {},
        cast(
            Context,
            SimpleNamespace(
                session=base.session,
                request_context=base.request_context,
                request_state=pending.request_state,
                input_responses={
                    "choice": SimpleNamespace(action="accept", content={"mode": "summary"}),
                    "other": SimpleNamespace(action="accept", content={"value": "unexpected"}),
                },
            ),
        ),
    )

    assert result.success is False


@pytest.mark.anyio
async def test_defaults_activate_and_resolve_a_conditional_follow_up_form() -> None:
    """Defaults must be reconsidered before a non-eliciting request completes."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose target.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "default": "branch"}},
                        "required": ["mode"],
                    },
                },
                "reference": {
                    "message": "Enter reference.",
                    "when": {"mode": "branch"},
                    "schema": {
                        "type": "object",
                        "properties": {"reference": {"type": "string", "default": "main"}},
                        "required": ["reference"],
                    },
                },
            }
        },
        {},
        None,
    )

    assert result == {"mode": "branch", "reference": "main"}


@pytest.mark.anyio
async def test_cancelled_defaults_preserve_an_explicit_uri_value() -> None:
    """Cancellation never replaces a value explicitly supplied by the caller."""
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses={"choice": SimpleNamespace(action="cancel", content=None)},
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )
    result = await resolve_elicitations(
        {
            "elicitation": {
                "choice": {
                    "message": "Choose.",
                    "schema": {
                        "type": "object",
                        "properties": {"mode": {"type": "string", "default": "default"}},
                        "required": ["mode"],
                    },
                }
            }
        },
        {"mode": "explicit"},
        cast(Context, context),
    )

    assert result == {"mode": "explicit"}


@pytest.mark.anyio
async def test_uri_values_are_normalised_before_conditional_matching() -> None:
    """URI strings use their declared primitive type for branching and rendering."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "count": {
                    "message": "Count.",
                    "schema": {"type": "object", "properties": {"count": {"type": "integer"}}, "required": ["count"]},
                },
                "detail": {
                    "message": "Detail.",
                    "when": {"count": 1},
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string", "default": "on"}},
                        "required": ["detail"],
                    },
                },
            }
        },
        {"count": "1"},
        None,
    )

    assert result == {"count": 1, "detail": "on"}


@pytest.mark.anyio
async def test_uri_boolean_coercion_preserves_literal_string_values() -> None:
    """A declared string form accepts the text parsed from a URI boolean literal."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "choice": {
                    "message": "Choose.",
                    "schema": {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]},
                }
            }
        },
        {"value": True},
        None,
    )

    assert result == {"value": "true"}


def test_cyclic_conditional_forms_are_rejected() -> None:
    """Cycles are declaration errors rather than incomplete interactive flows."""
    result = parse_elicitations(
        {
            "elicitation": {
                "first": {
                    "message": "First.",
                    "when": {"second": "yes"},
                    "schema": {"type": "object", "properties": {"first": {"type": "string"}}, "required": ["first"]},
                },
                "second": {
                    "message": "Second.",
                    "when": {"first": "yes"},
                    "schema": {"type": "object", "properties": {"second": {"type": "string"}}, "required": ["second"]},
                },
            }
        }
    )

    assert getattr(result, "success", None) is False


@pytest.mark.anyio
async def test_non_interactive_guidance_names_an_unresolved_condition_supplier() -> None:
    """Non-interactive callers need the supplier that determines a conditional form."""
    result = await resolve_elicitations(
        {
            "elicitation": {
                "target": {
                    "message": "Choose.",
                    "schema": {"type": "object", "properties": {"mode": {"type": "string"}}},
                },
                "reference": {
                    "message": "Reference.",
                    "when": {"mode": "branch"},
                    "schema": {
                        "type": "object",
                        "properties": {"reference": {"type": "string"}},
                        "required": ["reference"],
                    },
                },
            }
        },
        {},
        None,
    )

    assert getattr(result, "error", None) == "This entrypoint requires input; pass URI keywords: mode."


@pytest.mark.anyio
async def test_modern_continuation_rejects_a_different_entrypoint() -> None:
    """A continuation token is bound to the entrypoint that issued it."""
    frontmatter = {
        "elicitation": {
            "choice": {
                "message": "Choose.",
                "schema": {"type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]},
            }
        }
    }
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )
    pending = await resolve_elicitations(frontmatter, {}, cast(Context, context), entrypoint="skill:review")
    replay = await resolve_elicitations(
        frontmatter,
        {},
        cast(
            Context,
            SimpleNamespace(
                **context.__dict__,
                request_state=pending.request_state,
                input_responses={"choice": SimpleNamespace(action="accept", content={"mode": "summary"})},
            ),
        ),
        entrypoint="command:review",
    )

    assert replay.success is False


@pytest.mark.anyio
async def test_fractional_integer_response_is_coerced_before_conditional_matching(modern_elicitation_context) -> None:
    """Integer fields use the requested int coercion for accepted numeric values."""
    context = modern_elicitation_context(
        input_responses={"count": SimpleNamespace(action="accept", content={"count": 1.9})}
    )
    result = await resolve_elicitations(
        {
            "elicitation": {
                "count": {
                    "message": "Count.",
                    "schema": {"type": "object", "properties": {"count": {"type": "integer"}}, "required": ["count"]},
                },
                "detail": {
                    "message": "Detail.",
                    "when": {"count": 1},
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string", "default": "on"}},
                        "required": ["detail"],
                    },
                },
            }
        },
        {},
        context,
    )

    assert isinstance(result, InputRequiredResult)
    assert set(result.input_requests) == {"detail"}


@pytest.mark.anyio
async def test_legacy_optional_boolean_may_be_omitted() -> None:
    """Legacy form models represent omitted optional primitives as absent."""

    async def accept_required(_message: str, model: object) -> AcceptedElicitation[object]:
        return AcceptedElicitation(data=model(name="value"))  # type: ignore[operator]

    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2025-11-25"),
        elicit=accept_required,
    )
    result = await resolve_elicitations(
        {
            "elicitation": {
                "choice": {
                    "message": "Choose.",
                    "schema": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "enabled": {"type": "boolean"}},
                        "required": ["name"],
                    },
                }
            }
        },
        {},
        cast(Context, context),
    )

    assert result == {"name": "value"}
