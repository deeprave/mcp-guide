"""Tests for Result[T] pattern."""

import json

import pytest

from mcp_core.result import Result


class TestResultOk:
    """Tests for Result.ok() success cases."""

    def test_ok_creates_success_result(self):
        """Result.ok() should create a success result with value."""
        result = Result.ok("test_value")

        assert result.success is True
        assert result.value == "test_value"
        assert result.error is None


class TestResultFailure:
    """Tests for Result.failure() error cases."""

    def test_failure_creates_failure_result(self):
        """Result.failure() should create a failure result with error."""
        result = Result.failure("error message", error_type="validation")

        assert result.success is False
        assert result.error == "error message"
        assert result.error_type == "validation"
        assert result.value is None


class TestResultMethods:
    """Tests for Result helper methods."""

    def test_is_ok_returns_true_for_success(self):
        """is_ok() should return True for successful results."""
        result = Result.ok("value")
        assert result.is_ok() is True
        assert result.is_failure() is False

    def test_is_failure_returns_true_for_failure(self):
        """is_failure() should return True for failed results."""
        result = Result.failure("error")
        assert result.is_failure() is True
        assert result.is_ok() is False


class TestResultToJson:
    """Tests for Result JSON serialization."""

    def test_to_json_with_all_fields(self):
        """to_json() should include all relevant fields."""
        result = Result.ok("value")
        result.message = "info message"
        result.instruction = "do something"

        data = result.to_json()

        assert data["success"] is True
        assert data["value"] == "value"
        assert data["message"] == "info message"
        assert data["instruction"] == "do something"

    def test_to_json_str_serializes_to_json(self):
        """to_json_str() should return valid JSON string."""
        result = Result.ok({"key": "value"})

        json_str = result.to_json_str()
        parsed = json.loads(json_str)

        assert parsed["success"] is True
        assert parsed["value"] == {"key": "value"}

    def test_to_json_converts_exception_to_fields(self):
        """to_json() should convert exception to exception_type and exception_message."""
        exc = ValueError("test error")
        result = Result.failure("failed", exception=exc)

        data = result.to_json()

        assert data["exception_type"] == "ValueError"
        assert data["exception_message"] == "test error"

    def test_to_json_includes_instruction_field(self):
        """to_json() should include instruction field when present."""
        result = Result.failure("error")
        result.instruction = "Try using --force flag"

        data = result.to_json()

        assert data["instruction"] == "Try using --force flag"

    def test_to_json_includes_error_data(self):
        """to_json() should include error_data when present on failure."""
        error_data = {
            "validation_errors": [
                {"field": "name", "message": "Required field"},
                {"field": "age", "message": "Must be positive"},
            ]
        }
        result = Result.failure("Validation failed", error_type="validation_error")
        result.error_data = error_data

        data = result.to_json()

        assert data["error_data"] == error_data
        assert data["error"] == "Validation failed"
        assert data["error_type"] == "validation_error"

    def test_to_json_omits_error_data_when_none(self):
        """to_json() should not include error_data field when None."""
        result = Result.failure("Simple error")

        data = result.to_json()

        assert "error_data" not in data
