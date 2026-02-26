"""Plain content formatter for single file responses."""

from pathlib import Path

from mcp_guide.discovery.files import FileInfo


class PlainFormatter:
    """Formats file content as plain text without headers."""

    async def format(self, file_infos: list[FileInfo], docroot: Path) -> str:
        """Format file content as plain text.

        Args:
            file_infos: List of files with content
            docroot: Document root path (unused for plain format)

        Returns:
            Plain content without headers
        """
        if not file_infos:
            return ""

        if len(file_infos) == 1:
            return await self.format_single(file_infos[0])

        return await self.format_multiple(file_infos)

    async def format_single(self, file_info: FileInfo) -> str:
        """Format single file as plain content.

        Args:
            file_info: File with content

        Returns:
            Plain content without headers
        """
        return file_info.content or ""

    async def format_multiple(self, file_infos: list[FileInfo]) -> str:
        """Format multiple files with separators.

        Args:
            file_infos: List of files with content

        Returns:
            Concatenated content with separators
        """
        parts = []
        for file_info in file_infos:
            separator = f"--- {file_info.name} ---\n"
            content = file_info.content or ""
            parts.append(separator + content)
        return "\n".join(parts)
