"""Result handler decorators for validation and error handling."""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Optional, TypeVar

from mcp_guide.core.result import Result
from mcp_guide.core.validation import ArgValidationError

T = TypeVar("T")


def validate_result(
    success_instruction: Optional[str] = None,
    failure_instruction: Optional[str] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[Result[T]]]]:
    """Decorator to wrap async function results in Result type with validation error handling.

    Converts ArgValidationError exceptions into Result.failure, all other exceptions propagate.
    Only supports async functions.

    Args:
        success_instruction: Optional instruction to include in successful results
        failure_instruction: Optional instruction to include in failed results

    Returns:
        Decorator that wraps async function return values in Result

    Raises:
        TypeError: If decorated function is not async

    Example:
        @validate_result(success_instruction="Data validated successfully")
        async def process_data(data: str) -> str:
            validate_path(data)  # May raise ArgValidationError
            return data.upper()
    """
    import inspect

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[Result[T]]]:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(f"validate_result only supports async functions, got {fn.__name__}")

        @wraps(fn)
        async def wrapper(*args: object, **kwargs: object) -> Result[T]:
            try:
                data = await fn(*args, **kwargs)
                result = Result.ok(data)
                if success_instruction:
                    result.instruction = success_instruction
                return result
            except ArgValidationError as e:
                result = e.to_result()
                if failure_instruction:
                    result.instruction = failure_instruction
                return result

        return wrapper

    return decorator
