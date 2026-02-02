"""Shared utilities for requires-* directive checking."""

from typing import Any


def check_requires_directive(required_value: Any, actual_value: Any) -> bool:
    """Check if a requires-* directive is satisfied.

    Supports three checking modes:
    1. Boolean mode: Check if actual_value is truthy/falsy
    2. List membership mode: Check if ANY required item is in actual_value (OR logic)
    3. Exact match mode: Check if values are equal

    Args:
        required_value: The value specified in the requires-* directive
        actual_value: The actual value from project flags/context

    Returns:
        True if requirement is satisfied, False otherwise

    Examples:
        >>> check_requires_directive(True, "some_value")
        True
        >>> check_requires_directive(False, None)
        True
        >>> check_requires_directive(["discussion"], ["discussion", "planning"])
        True
        >>> check_requires_directive(["deployment"], ["discussion", "planning"])
        False
        >>> check_requires_directive(["implementation"], {"implementation": ["entry"]})
        True
    """
    # Boolean mode: check truthy/falsy
    if isinstance(required_value, bool):
        return bool(actual_value) == required_value

    # List membership mode: ANY match (OR logic)
    if isinstance(required_value, list):
        # Scalar actual_value: check if it's in the required list
        if not isinstance(actual_value, (list, dict)):
            return actual_value in required_value

        # List actual_value: check if ANY required item is in actual list
        if isinstance(actual_value, list):
            return any(item in actual_value for item in required_value)

        # Dict actual_value: check if ANY required key exists in dict
        if isinstance(actual_value, dict):
            return any(key in actual_value for key in required_value)

    # Exact match mode: fallback for other types
    return bool(actual_value == required_value)
