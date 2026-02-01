"""MIME content formatter for single and multiple file responses."""

import mimetypes

from uuid_extensions import uuid7

from mcp_guide.discovery.files import FileInfo


class MimeFormatter:
    """Formats file content with MIME headers."""

    async def format(self, file_infos: list[FileInfo], category_name: str) -> str:
        """Format file content with MIME headers.

        Args:
            file_infos: List of files with content
            category_name: Name of the category

        Returns:
            Formatted content with MIME headers
        """
        if not file_infos:
            return ""

        if len(file_infos) == 1:
            return await self.format_single(file_infos[0], category_name)

        return await self.format_multiple(file_infos, category_name)

    async def format_single(self, file_info: FileInfo, category_name: str) -> str:
        """Format single file with MIME headers.

        Args:
            file_info: File with content
            category_name: Name of the category

        Returns:
            Formatted content with MIME headers
        """
        content = file_info.content or ""

        # Detect Content-Type
        mime_type, _ = mimetypes.guess_type(file_info.name)
        content_type = mime_type or "text/plain"

        # Build Content-Location
        content_location = f"guide://category/{category_name}/{file_info.path}"

        # Calculate Content-Length from final rendered content
        content_length = len(content.encode("utf-8"))

        # Build headers
        headers = f"Content-Type: {content_type}\r\n"
        headers += f"Content-Location: {content_location}\r\n"
        headers += f"Content-Length: {content_length}\r\n"

        # Return headers + blank line + content
        return headers + "\r\n" + content

    async def format_multiple(self, file_infos: list[FileInfo], category_name: str) -> str:
        """Format multiple files as multipart/mixed.

        Args:
            file_infos: List of files with content
            category_name: Name of the category

        Returns:
            RFC 2046 multipart/mixed formatted content
        """
        # Generate boundary using UUID7 (time-ordered)
        boundary = f"guide-boundary-{uuid7()}"

        # Build main header
        result = f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n\r\n'

        # Build each part
        for file_info in file_infos:
            content = file_info.content or ""

            # Detect Content-Type
            mime_type, _ = mimetypes.guess_type(file_info.name)
            content_type = mime_type or "text/plain"

            # Build Content-Location
            content_location = f"guide://category/{category_name}/{file_info.path}"

            # Calculate Content-Length from final rendered content
            content_length = len(content.encode("utf-8"))

            # Add boundary and headers for this part
            result += f"--{boundary}\r\n"
            result += f"Content-Type: {content_type}\r\n"
            result += f"Content-Location: {content_location}\r\n"
            result += f"Content-Length: {content_length}\r\n"
            result += "\r\n"
            result += content
            result += "\r\n"

        # Add closing boundary
        result += f"--{boundary}--\r\n"

        return result
