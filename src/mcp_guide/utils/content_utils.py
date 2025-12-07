"""Shared utilities for content retrieval tools."""

from pathlib import Path
from typing import Optional

from mcp_core.file_reader import read_file_content
from mcp_core.path_security import resolve_safe_path
from mcp_core.result import Result
from mcp_guide.utils.file_discovery import FileInfo


def resolve_patterns(override_pattern: Optional[str], default_patterns: list[str]) -> list[str]:
    """Resolve patterns with optional override.

    Args:
        override_pattern: Optional pattern to override defaults
        default_patterns: Default patterns to use if no override

    Returns:
        List of patterns to use
    """
    return [override_pattern] if override_pattern else default_patterns


async def read_file_contents(
    files: list[FileInfo],
    base_dir: Path,
    category_prefix: Optional[str] = None,
) -> list[str]:
    """Read content for FileInfo objects and optionally prefix basenames.

    Args:
        files: List of FileInfo objects to read
        base_dir: Base directory for resolving file paths
        category_prefix: Optional prefix to add to basenames (e.g., "category")

    Returns:
        List of error messages for files that failed to read
    """
    file_read_errors: list[str] = []

    for file_info in files:
        try:
            file_path = resolve_safe_path(base_dir, file_info.path)
            file_info.content = await read_file_content(file_path)

            if category_prefix:
                file_info.basename = f"{category_prefix}/{file_info.basename}"

        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            error_path = f"{category_prefix}/{file_info.basename}" if category_prefix else file_info.basename
            file_read_errors.append(f"'{error_path}': {e}")

    return file_read_errors


def create_file_read_error_result(
    errors: list[str],
    context_name: str,
    context_type: str,
    error_type: str,
    instruction: str,
) -> Result[str]:
    """Create standardized file read error result.

    Args:
        errors: List of error messages
        context_name: Name of the category or collection
        context_type: Type of context ("category" or "collection")
        error_type: Error type constant
        instruction: Instruction constant

    Returns:
        Result object with error
    """
    error_message = f"Failed to read one or more files in {context_type} '{context_name}': " + "; ".join(errors)
    error_result: Result[str] = Result.failure(
        error_message,
        error_type=error_type,
        instruction=instruction,
    )
    return error_result
