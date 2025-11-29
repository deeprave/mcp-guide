"""Result handler decorator for validation errors."""

from functools import wraps
from typing import Callable, Optional, TypeVar

from mcp_core.result import Result
from mcp_core.validation import ValidationError

T = TypeVar("T")


def validate_result(
    message: Optional[str] = None,
    success_instruction: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., Result[T]]]:
    """Decorator to convert ValidationError exceptions to Result[T].

    Args:
        message: Optional message to set on result
        success_instruction: Optional instruction for successful results

    Returns:
        Decorated function that returns Result[T]
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., Result[T]]:
        @wraps(fn)
        def wrapper(*args: object, **kwargs: object) -> Result[T]:
            try:
                data = fn(*args, **kwargs)
                result = Result.ok(data)
                if success_instruction:
                    result.instruction = success_instruction
            except ValidationError as e:
                result = Result.failure(e.message, error_type=e.error_type)
                result.instruction = e.instruction

            if message:
                result.message = message
            return result

        return wrapper

    return decorator
