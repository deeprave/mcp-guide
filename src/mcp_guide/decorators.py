"""Decorators for automatic task initialization."""

from typing import TYPE_CHECKING, Any, Set, Type, TypeVar

if TYPE_CHECKING:
    pass

T = TypeVar("T")

# Track which classes have been instantiated to prevent duplicates
_instantiated_classes: Set[Type[Any]] = set()


def task_init(cls: Type[T]) -> Type[T]:
    """Decorator that automatically instantiates a class during import.

    This ensures task managers are created when their modules are imported,
    triggering any initialization logic in their __init__ methods.

    Args:
        cls: The class to auto-instantiate

    Returns:
        The original class (unmodified)
    """
    # Check if already instantiated to prevent duplicates from multiple imports
    if cls in _instantiated_classes:
        return cls

    _instantiated_classes.add(cls)

    # Simply instantiate the class - let its __init__ handle everything
    logger = __import__("mcp_guide.core.mcp_log", fromlist=["get_logger"]).get_logger(__name__)
    logger.trace(f"@task_init: Instantiating {cls.__name__}")
    # IMPORTANT: Instance must subscribe to TaskManager in __init__ to avoid garbage collection
    # The subscription keeps a reference to the instance, preventing it from being collected
    instance = cls()
    logger.trace(f"@task_init: Created {cls.__name__} instance: {instance}")
    return cls
