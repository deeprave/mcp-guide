from contextvars import ContextVar
from typing import Callable, TypeVar

T = TypeVar("T")


def get_or_create(var: ContextVar[T], factory: Callable[[], T]) -> T:
    """Get the value of a ContextVar, creating and storing it via factory if unset.

    Uses Token.MISSING to detect absence, so ContextVars with a default value are
    handled correctly (the factory is still called on first use per-task).
    """
    try:
        return var.get()
    except LookupError:
        value = factory()
        var.set(value)
        return value
