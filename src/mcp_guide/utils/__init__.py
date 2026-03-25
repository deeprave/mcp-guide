from contextvars import ContextVar
from typing import Callable, TypeVar

T = TypeVar("T")


def get_or_create(var: ContextVar[T], factory: Callable[[], T]) -> T:
    """Get the value of a ContextVar, creating and storing it via factory if unset.

    If the ContextVar has no value set and no default, calls factory() to create
    a value, stores it via var.set(), and returns it. If the ContextVar already
    has a value or a default, returns that directly without calling factory.
    """
    try:
        return var.get()
    except LookupError:
        value = factory()
        var.set(value)
        return value
