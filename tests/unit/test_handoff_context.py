"""Behavioural tests for handoff-context flag resolution."""

import pytest

from mcp_guide.feature_flags.constants import FLAG_HANDOFF_CONTEXT
from mcp_guide.feature_flags.resolution import resolve_flag
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validators import FlagValidationError, normalise_flag, validate_flag_with_registered
from mcp_guide.handoff_context import resolve_handoff_context


@pytest.mark.parametrize("value", [True, False, "true", "false", "notes.md", ".state/context.txt"])
def test_handoff_context_flag_accepts_boolean_or_relative_target(value):
    validate_flag_with_registered(FLAG_HANDOFF_CONTEXT, value, is_project=True)
    validate_flag_with_registered(FLAG_HANDOFF_CONTEXT, value, is_project=False)


@pytest.mark.parametrize(
    "value", ["", "   ", "/tmp/context.json", "~/context.json", "~unknown/context.json", "../context.json", "docs/"]
)
def test_handoff_context_flag_rejects_invalid_or_absolute_target(value):
    with pytest.raises(FlagValidationError):
        validate_flag_with_registered(FLAG_HANDOFF_CONTEXT, value, is_project=True)


def test_handoff_context_flag_normalises_boolean_like_values():
    assert normalise_flag(FLAG_HANDOFF_CONTEXT, "enabled") == True
    assert normalise_flag(FLAG_HANDOFF_CONTEXT, "off") == False
    assert normalise_flag(FLAG_HANDOFF_CONTEXT, "notes.md") == "notes.md"


def test_project_handoff_context_overrides_global_value():
    global_value = FeatureValue(True)
    project_value = FeatureValue("notes.md")

    assert (
        resolve_flag(FLAG_HANDOFF_CONTEXT, {FLAG_HANDOFF_CONTEXT: project_value}, {FLAG_HANDOFF_CONTEXT: global_value})
        is project_value
    )


@pytest.mark.parametrize(
    ("value", "target", "format", "eligible"),
    [
        (None, None, None, False),
        (False, None, None, False),
        (True, ".todo/context.json", "JSON", True),
        ("notes.md", ".todo/notes.md", "Markdown", True),
        ("state/context.txt", "state/context.txt", "plain text", True),
        ("private/context.yaml", "private/context.yaml", "YAML", False),
    ],
)
def test_resolve_handoff_context_selects_target_format_and_write_eligibility(value, target, format, eligible):
    resolved = resolve_handoff_context(value, documents_path=".todo/", allowed_write_paths=[".todo/", "state/"])

    assert resolved.target == target
    assert resolved.format == format
    assert resolved.eligible is eligible
