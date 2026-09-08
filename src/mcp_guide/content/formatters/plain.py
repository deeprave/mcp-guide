"""Plain content formatter for single file responses."""

from collections.abc import Callable
from pathlib import Path

from mcp_guide.content_limits import BoundedTextAccumulator
from mcp_guide.discovery.files import FileInfo


class PlainFormatter:
    """Formats file content as plain text without headers."""

    async def format(
        self,
        file_infos: list[FileInfo],
        resolve_document_path: Callable[[str | Path], Path],
        *,
        max_content_limit: int | None = None,
    ) -> str:
        """Format file content as plain text.

        Args:
            file_infos: List of files with content
            resolve_document_path: Sync document-root-relative path resolver

        Returns:
            Plain content without headers
        """
        if not file_infos:
            return ""

        if len(file_infos) == 1:
            return await self.format_single(file_infos[0], max_content_limit=max_content_limit)

        return await self.format_multiple(file_infos, max_content_limit=max_content_limit)

    async def format_single(self, file_info: FileInfo, *, max_content_limit: int | None = None) -> str:
        """Format single file as plain content.

        Args:
            file_info: File with content

        Returns:
            Plain content without headers
        """
        content = file_info.content or ""
        if max_content_limit is None:
            return content
        accumulator = BoundedTextAccumulator(max_content_limit)
        accumulator.append(content)
        return accumulator.render()

    async def format_multiple(self, file_infos: list[FileInfo], *, max_content_limit: int | None = None) -> str:
        """Format multiple files with separators.

        Args:
            file_infos: List of files with content

        Returns:
            Concatenated content with separators
        """
        if max_content_limit is None:
            parts = []
            for file_info in file_infos:
                separator = f"--- {file_info.name} ---\n"
                content = file_info.content or ""
                parts.append(separator + content)
            return "\n".join(parts)

        accumulator = BoundedTextAccumulator(max_content_limit)
        for index, file_info in enumerate(file_infos):
            separator = f"--- {file_info.name} ---\n"
            content = file_info.content or ""
            if index:
                accumulator.append("\n")
            accumulator.append(separator)
            accumulator.append(content)
        return accumulator.render()
