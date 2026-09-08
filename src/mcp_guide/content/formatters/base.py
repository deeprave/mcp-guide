"""Base content formatter that merges content with newline separators."""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from mcp_guide.content_limits import BoundedTextAccumulator

if TYPE_CHECKING:
    from mcp_guide.discovery.files import FileInfo


class BaseFormatter:
    """Formatter that merges file content with newline separators."""

    async def format(
        self,
        files: list["FileInfo"],
        resolve_document_path: Callable[[str | Path], Path],
        *,
        max_content_limit: int | None = None,
    ) -> str:
        """Format files by concatenating content with newline separators.

        Args:
            files: List of FileInfo objects to format
            resolve_document_path: Sync document-root-relative path resolver

        Returns:
            Concatenated file contents separated by newlines
        """
        if max_content_limit is None:
            return "\n".join(file.content or "" for file in files)
        accumulator = BoundedTextAccumulator(max_content_limit)
        for index, file in enumerate(files):
            if index:
                accumulator.append("\n")
            accumulator.append(file.content or "")
        return accumulator.render()
