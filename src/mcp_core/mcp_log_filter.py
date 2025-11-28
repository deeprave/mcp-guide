"""PII redaction stub for MCP logging.

This module provides a placeholder for future PII redaction functionality.
Currently returns a pass-through function that does not modify log messages.

Future integration points:
- AWS Comprehend PII detection
- Custom regex-based redaction
- Configurable redaction policies
"""

from typing import Callable


def get_redaction_function() -> Callable[[str], str]:
    """Get the redaction function for log messages.

    Returns a callable that accepts a string and returns a string.
    Currently returns a pass-through function (no redaction).

    Returns:
        Callable that takes a string and returns the same string unchanged.
    """
    return lambda message: message
