from contextvars import ContextVar
from typing import Callable, TypeVar

T = TypeVar("T")

_MISSING = object()


def get_or_create(var: ContextVar[T], factory: Callable[[], T]) -> T:
    """Get the value of a ContextVar, creating and storing it via factory if unset.

    Uses a sentinel to detect absence, so ContextVars with a default value are
    handled correctly (the factory is still called on first use per-task).
    """
    value = var.get(_MISSING)
    if value is _MISSING:
        value = factory()
        var.set(value)
    return value  # type: ignore[return-value]
