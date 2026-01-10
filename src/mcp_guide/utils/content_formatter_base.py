"""Base content formatter that merges content without separators."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_guide.utils.file_discovery import FileInfo


class BaseFormatter:
    """Formatter that merges file content without separators."""

    async def format(self, files: list["FileInfo"], context_name: str) -> str:
        """Format files by concatenating content without separators.

        Args:
            files: List of FileInfo objects to format
            context_name: Name for context (unused in base formatter)

        Returns:
            Concatenated file contents
        """
        return "".join(file.content or "" for file in files)
