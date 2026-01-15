"""Decorators for automatic task initialization."""

from typing import Type, TypeVar

T = TypeVar("T")


def task_init(cls: Type[T]) -> Type[T]:
    """Decorator that automatically instantiates a class during import.

    This ensures task managers are created when their modules are imported,
    triggering any initialization logic in their __init__ methods.

    Args:
        cls: The class to auto-instantiate

    Returns:
        The original class (unmodified)
    """
    # Simply instantiate the class - let its __init__ handle everything
    logger = __import__("mcp_core.mcp_log", fromlist=["get_logger"]).get_logger(__name__)
    logger.trace(f"@task_init: Instantiating {cls.__name__}")
    instance = cls()
    logger.trace(f"@task_init: Created {cls.__name__} instance: {instance}")
    return cls
