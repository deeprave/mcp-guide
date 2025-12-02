"""Core reusable functionality for MCP servers."""

from mcp_core.file_reader import read_file_content
from mcp_core.result_handler import validate_result
from mcp_core.validation import (
    ArgValidationError,
    is_absolute_path,
    validate_description,
    validate_directory_path,
    validate_pattern,
)

__all__ = [
    "ArgValidationError",
    "is_absolute_path",
    "read_file_content",
    "validate_description",
    "validate_directory_path",
    "validate_pattern",
    "validate_result",
]

__version__ = "0.5.0"

__all__ = [
    "ArgValidationError",
    "is_absolute_path",
    "read_file_content",
    "validate_description",
    "validate_directory_path",
    "validate_pattern",
    "validate_result",
]
