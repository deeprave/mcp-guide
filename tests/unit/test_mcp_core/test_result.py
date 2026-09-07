"""Rich Result factories and public JSON representation."""

import json

import pytest

from mcp_guide.core.result import Result


def test_success_factory_preserves_agent_fields_in_dict_and_json():
    result = Result.ok(
        {"key": "value"},
        message="info",
        arguments="args",
        instruction="Read this",
        disposition="agent/instruction",
        additional_agent_instructions="Follow up",
    )
    assert result.is_ok() and not result.is_failure()
    assert result.error is None
    expected = {
        "success": True,
        "value": {"key": "value"},
        "message": "info",
        "arguments": "args",
        "instruction": "Read this",
        "disposition": "agent/instruction",
        "additional_agent_instructions": "Follow up",
    }
    assert result.to_json() == expected
    assert json.loads(result.to_json_str()) == expected


def test_failure_factory_serialises_error_details_and_guidance():
    details = {"validation_errors": [{"field": "name", "message": "Required"}]}
    result = Result.failure(
        "Validation failed",
        error_type="validation",
        exception=ValueError("Required"),
        instruction="Fix the name",
        error_data=details,
        disposition="agent/information",
    )
    assert result.is_failure() and not result.is_ok()
    assert result.value is None
    expected = {
        "success": False,
        "error": "Validation failed",
        "error_type": "validation",
        "exception_type": "ValueError",
        "exception_message": "Required",
        "instruction": "Fix the name",
        "error_data": details,
        "disposition": "agent/information",
    }
    assert result.to_json() == expected
    assert json.loads(result.to_json_str()) == expected


@pytest.mark.parametrize(
    "factory", [lambda: Result.ok(), lambda: Result.failure("Simple error")], ids=["success", "failure"]
)
def test_absent_optional_data_is_not_serialised(factory):
    result = factory()
    payload = result.to_json()
    assert {
        "value",
        "disposition",
        "error_data",
        "exception_type",
        "exception_message",
        "message",
        "arguments",
    }.isdisjoint(payload)
    assert result.disposition is None
