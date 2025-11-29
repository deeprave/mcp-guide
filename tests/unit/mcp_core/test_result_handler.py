"""Tests for result handler decorator."""

import pytest

from mcp_core.result_handler import validate_result
from mcp_core.validation import ValidationError


class TestValidateResult:
    """Tests for validate_result decorator."""

    def test_success_returns_ok_result(self):
        """Successful function returns Result.ok."""

        @validate_result()
        def success_fn() -> str:
            return "success"

        result = success_fn()
        assert result.is_ok()
        assert result.value == "success"

    def test_validation_error_returns_failure_result(self):
        """ValidationError is caught and converted to Result.failure."""

        @validate_result()
        def error_fn() -> str:
            raise ValidationError("test error", error_type="test_type")

        result = error_fn()
        assert result.is_failure()
        assert result.error == "test error"
        assert result.error_type == "test_type"

    def test_instruction_preserved_from_validation_error(self):
        """Instruction from ValidationError is preserved in result."""

        @validate_result()
        def error_fn() -> str:
            raise ValidationError("error", error_type="test", instruction="custom instruction")

        result = error_fn()
        assert result.instruction == "custom instruction"

    def test_success_instruction_applied(self):
        """Success instruction is applied to ok results."""

        @validate_result(success_instruction="do this next")
        def success_fn() -> str:
            return "data"

        result = success_fn()
        assert result.instruction == "do this next"

    def test_message_applied_to_result(self):
        """Message parameter is applied to result."""

        @validate_result(message="operation complete")
        def success_fn() -> str:
            return "data"

        result = success_fn()
        assert result.message == "operation complete"

    def test_message_applied_to_failure(self):
        """Message parameter is applied to failure results."""

        @validate_result(message="operation failed")
        def error_fn() -> str:
            raise ValidationError("error")

        result = error_fn()
        assert result.message == "operation failed"

    def test_function_arguments_passed_through(self):
        """Function arguments are passed through correctly."""

        @validate_result()
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        assert result.value == 5

    def test_function_kwargs_passed_through(self):
        """Function kwargs are passed through correctly."""

        @validate_result()
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}"

        result = greet("World", greeting="Hi")
        assert result.value == "Hi, World"
