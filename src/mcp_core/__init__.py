"""Core reusable functionality for MCP servers."""

from mcp_core.result_handler import validate_result
from mcp_core.validation import (
    ValidationError,
    is_absolute_path,
    validate_description,
    validate_directory_path,
    validate_pattern,
)

__version__ = "0.5.0"

__all__ = [
    "ValidationError",
    "is_absolute_path",
    "validate_description",
    "validate_directory_path",
    "validate_pattern",
    "validate_result",
]
