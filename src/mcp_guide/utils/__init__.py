from contextvars import ContextVar
from typing import Callable, TypeVar

T = TypeVar("T")


def get_or_create(var: ContextVar[T], factory: Callable[[], T]) -> T:
    """Get the value of a ContextVar, creating and storing it via factory if absent."""
    try:
        return var.get()
    except LookupError:
        instance = factory()
        var.set(instance)
        return instance
