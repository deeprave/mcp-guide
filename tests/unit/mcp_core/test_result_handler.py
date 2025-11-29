"""Tests for result handler decorator."""

import pytest

from mcp_core.result_handler import validate_result
from mcp_core.validation import ValidationError


@pytest.mark.asyncio
async def test_non_validation_error_is_propagated():
    """Non-ValidationError exceptions should propagate unchanged."""

    @validate_result()
    async def error_fn() -> str:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await error_fn()


def test_sync_function_raises_type_error():
    """Decorating a sync function should raise TypeError."""
    with pytest.raises(TypeError, match="only supports async functions"):

        @validate_result()
        def sync_fn() -> str:
            return "sync"


class TestValidateResult:
    """Tests for validate_result decorator."""

    @pytest.mark.asyncio
    async def test_success_returns_ok_result(self):
        """Successful function returns Result.ok."""

        @validate_result()
        async def success_fn() -> str:
            return "success"

        result = await success_fn()
        assert result.is_ok()
        assert result.value == "success"

    @pytest.mark.asyncio
    async def test_validation_error_returns_failure_result(self):
        """ValidationError is caught and wrapped in Result.failure."""

        @validate_result()
        async def error_fn() -> str:
            raise ValidationError("Invalid input", error_type="validation")

        result = await error_fn()
        assert result.is_failure()
        assert result.error == "Invalid input"
        assert result.error_type == "validation"

    @pytest.mark.asyncio
    async def test_success_instruction_added(self):
        """Success instruction is added to successful results."""

        @validate_result(success_instruction="All good")
        async def success_fn() -> str:
            return "data"

        result = await success_fn()
        assert result.instruction == "All good"

    @pytest.mark.asyncio
    async def test_failure_instruction_added(self):
        """Failure instruction is added to failed results."""

        @validate_result(failure_instruction="Fix the error")
        async def error_fn() -> str:
            raise ValidationError("Bad data", error_type="validation")

        result = await error_fn()
        assert result.instruction == "Fix the error"
