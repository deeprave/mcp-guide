"""Core reusable functionality for MCP servers."""

from mcp_core.file_reader import read_file_content
from mcp_core.path_security import is_path_within_directory, resolve_safe_path
from mcp_core.result_handler import validate_result
from mcp_core.validation import (
    ArgValidationError,
    is_absolute_path,
    validate_description,
    validate_directory_path,
    validate_pattern,
)

__version__ = "0.5.0"

__all__ = [
    "ArgValidationError",
    "is_absolute_path",
    "is_path_within_directory",
    "read_file_content",
    "resolve_safe_path",
    "validate_description",
    "validate_directory_path",
    "validate_pattern",
    "validate_result",
]
