"""Base content formatter that merges content with newline separators."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_guide.discovery.files import FileInfo


class BaseFormatter:
    """Formatter that merges file content with newline separators."""

    async def format(self, files: list["FileInfo"], docroot: Path) -> str:
        """Format files by concatenating content with newline separators.

        Args:
            files: List of FileInfo objects to format
            docroot: Document root path (unused in base formatter)

        Returns:
            Concatenated file contents separated by newlines
        """
        return "\n".join(file.content or "" for file in files)
