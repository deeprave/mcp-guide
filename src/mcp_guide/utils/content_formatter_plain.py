"""Plain content formatter for single file responses."""

from mcp_guide.utils.file_discovery import FileInfo


class PlainFormatter:
    """Formats file content as plain text without headers."""

    async def format(self, file_infos: list[FileInfo], category_name: str) -> str:
        """Format file content as plain text.

        Args:
            file_infos: List of files with content
            category_name: Name of the category (unused for plain format)

        Returns:
            Plain content without headers
        """
        if not file_infos:
            return ""

        if len(file_infos) == 1:
            return await self.format_single(file_infos[0], category_name)

        return await self.format_multiple(file_infos, category_name)

    async def format_single(self, file_info: FileInfo, category_name: str) -> str:
        """Format single file as plain content.

        Args:
            file_info: File with content
            category_name: Name of the category (unused for plain format)

        Returns:
            Plain content without headers
        """
        return file_info.content or ""

    async def format_multiple(self, file_infos: list[FileInfo], category_name: str) -> str:
        """Format multiple files with separators.

        Args:
            file_infos: List of files with content
            category_name: Name of the category (unused for plain format)

        Returns:
            Concatenated content with separators
        """
        parts = []
        for file_info in file_infos:
            separator = f"--- {file_info.basename} ---\n"
            content = file_info.content or ""
            parts.append(separator + content)
        return "\n".join(parts)
