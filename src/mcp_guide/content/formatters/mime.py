"""MIME content formatter for single and multiple file responses."""

import csv
import io
import json
import re
import tomllib
from pathlib import Path

from uuid_extensions import uuid7

from mcp_guide.discovery.files import TEMPLATE_EXTENSIONS, FileInfo


class MimeFormatter:
    """Formats file content with MIME headers."""

    def _detect_text_subtype(self, content: str) -> str:
        """Detect specific text subtype from content.

        Args:
            content: File content (without frontmatter)

        Returns:
            MIME type string (e.g., 'text/markdown', 'text/csv', 'application/json')
        """
        content = content.strip()
        if not content:
            return "text/plain"

        # JSON: strict parse
        if content[0] in ("{", "[", '"'):
            try:
                json.loads(content)
                return "application/json"
            except json.JSONDecodeError:
                pass

        # TOML: strict parse (must fail JSON first)
        try:
            result = tomllib.loads(content)
            if result:  # Require at least one key
                return "application/toml"
        except tomllib.TOMLDecodeError:
            pass

        # CSV: sniff for delimited structure
        try:
            sample = "\n".join(content.splitlines()[:20])
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
            reader = csv.reader(io.StringIO(content), dialect)
            rows = [row for _, row in zip(range(5), reader)]
            col_counts = [len(r) for r in rows]
            if len(rows) >= 2 and max(col_counts) >= 2 and min(col_counts) >= 2:
                return "text/csv"
        except (csv.Error, Exception):
            pass

        # YAML: strict parse (JSON already ruled out)
        try:
            import yaml

            result = yaml.safe_load(content)
            if isinstance(result, (dict, list)):
                return "text/yaml"
        except (yaml.YAMLError, ImportError):
            pass

        # Markdown: heuristic pattern match
        markdown_patterns = [
            r"^#{1,6}\s+\S",  # ATX headings
            r"^\s*[-*+]\s+\S",  # Unordered lists
            r"^\s*\d+\.\s+\S",  # Ordered lists
            r"^```",  # Fenced code blocks
            r"\*\*.+\*\*",  # Bold
            r"\[.+\]\(.+\)",  # Links
        ]
        lines = content.splitlines()
        matches = sum(1 for line in lines if any(re.search(p, line, re.MULTILINE) for p in markdown_patterns))
        if matches >= 2 or (len(lines) > 0 and matches / len(lines) > 0.1):
            return "text/markdown"

        return "text/plain"

    def _get_appropriate_extension(self, detected_type: str) -> str:
        """Get file extension for detected content type.

        Args:
            detected_type: MIME type string

        Returns:
            File extension (e.g., '.json', '.md')
        """
        type_to_ext = {
            "application/json": ".json",
            "application/toml": ".toml",
            "text/csv": ".csv",
            "text/yaml": ".yaml",
            "text/markdown": ".md",
        }
        return type_to_ext.get(detected_type, "")

    async def _get_relative_path(self, file_info: FileInfo, docroot: Path) -> Path:
        """Get relative path within category directory.

        Args:
            file_info: File information with category object set
            docroot: Document root path

        Returns:
            Relative path within category directory

        Raises:
            ValueError: If absolute path cannot be converted to relative
        """
        path = Path(file_info.path)

        # If already relative, return as-is
        if not path.is_absolute():
            return path

        # Must have category to convert absolute path
        if not file_info.category:
            raise ValueError(f"Cannot convert absolute path to relative: file has no category: {path}")

        # Get category directory
        category_dir = docroot / file_info.category.dir

        # Convert to relative
        try:
            return path.relative_to(category_dir)
        except ValueError as e:
            raise ValueError(f"Path is outside category directory: {path}") from e

    async def format(self, file_infos: list[FileInfo], docroot: Path) -> str:
        """Format file content with MIME headers.

        Args:
            file_infos: List of files with content and category set
            docroot: Document root path

        Returns:
            Formatted content with MIME headers
        """
        if not file_infos:
            return ""

        if len(file_infos) == 1:
            return await self.format_single(file_infos[0], docroot)

        return await self.format_multiple(file_infos, docroot)

    async def format_single(self, file_info: FileInfo, docroot: Path) -> str:
        """Format single file with MIME headers.

        Args:
            file_info: File with content and category set
            docroot: Document root path

        Returns:
            Formatted content with MIME headers
        """
        if not file_info.category:
            raise ValueError("File must have category set for MIME formatting")

        content = file_info.content or ""

        # Get relative path within category
        doc_path = await self._get_relative_path(file_info, docroot)
        doc_path_str = str(doc_path)

        # Strip template extensions
        for ext in TEMPLATE_EXTENSIONS:
            if doc_path_str.endswith(ext):
                doc_path_str = doc_path_str[: -len(ext)]
                break

        # Detect content type and add appropriate extension if needed
        detected_type = self._detect_text_subtype(content)
        appropriate_ext = self._get_appropriate_extension(detected_type)

        if appropriate_ext and not doc_path_str.endswith(appropriate_ext):
            doc_path_str += appropriate_ext

        # Build Content-Location with correct URI scheme using category name
        content_location = f"guide://{file_info.category.name}/{doc_path_str}"

        # Calculate Content-Length from final rendered content
        content_length = len(content.encode("utf-8"))

        # Build headers
        headers = f"Content-Type: {detected_type}\r\n"
        headers += f"Content-Location: {content_location}\r\n"
        headers += f"Content-Length: {content_length}\r\n"

        # Return headers + blank line + content
        return headers + "\r\n" + content

    async def format_multiple(self, file_infos: list[FileInfo], docroot: Path) -> str:
        """Format multiple files as multipart/mixed.

        Args:
            file_infos: List of files with content and category set
            docroot: Document root path

        Returns:
            RFC 2046 multipart/mixed formatted content
        """
        # Generate boundary using UUID7 (time-ordered)
        boundary = f"guide-boundary-{uuid7()}"

        # Build main header
        result = f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n\r\n'

        # Build each part
        for file_info in file_infos:
            if not file_info.category:
                raise ValueError("File must have category set for MIME formatting")

            content = file_info.content or ""

            # Get relative path within category
            doc_path = await self._get_relative_path(file_info, docroot)
            doc_path_str = str(doc_path)

            # Strip template extensions
            for ext in TEMPLATE_EXTENSIONS:
                if doc_path_str.endswith(ext):
                    doc_path_str = doc_path_str[: -len(ext)]
                    break

            # Detect content type and add appropriate extension if needed
            detected_type = self._detect_text_subtype(content)
            appropriate_ext = self._get_appropriate_extension(detected_type)

            if appropriate_ext and not doc_path_str.endswith(appropriate_ext):
                doc_path_str += appropriate_ext

            # Build Content-Location with correct URI scheme using category name
            content_location = f"guide://{file_info.category.name}/{doc_path_str}"

            # Calculate Content-Length from final rendered content
            content_length = len(content.encode("utf-8"))

            # Add boundary and headers for this part
            result += f"--{boundary}\r\n"
            result += f"Content-Type: {detected_type}\r\n"
            result += f"Content-Location: {content_location}\r\n"
            result += f"Content-Length: {content_length}\r\n"
            result += "\r\n"
            result += content
            result += "\r\n"

        # Add closing boundary
        result += f"--{boundary}--\r\n"

        return result
