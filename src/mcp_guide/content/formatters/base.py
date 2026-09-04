"""Base content formatter that merges content with newline separators."""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_guide.discovery.files import FileInfo


class BaseFormatter:
    """Formatter that merges file content with newline separators."""

    async def format(self, files: list["FileInfo"], resolve_document_path: Callable[[str | Path], Path]) -> str:
        """Format files by concatenating content with newline separators.

        Args:
            files: List of FileInfo objects to format
            resolve_document_path: Sync document-root-relative path resolver

        Returns:
            Concatenated file contents separated by newlines
        """
        return "\n".join(file.content or "" for file in files)
