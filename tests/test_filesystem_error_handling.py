"""Tests for filesystem error handling."""

from unittest.mock import patch

import pytest

from mcp_guide.filesystem.path_validator import SecurityError
from mcp_guide.tools.tool_filesystem import (
    SendFileContentArgs,
    internal_send_file_content,
)


class TestFileNotFoundErrors:
    """Tests for file not found error scenarios."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_file_not_found_error_handling(self, mock_send):
        """Should handle file not found with clear error message."""
        mock_send.side_effect = FileNotFoundError("File not found: /docs/missing.md")

        args = SendFileContentArgs(path="/docs/missing.md", content="")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "File not found" in result.error

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_directory_not_found_error_handling(self, mock_send):
        """Should handle directory not found with clear error message."""
        mock_send.side_effect = FileNotFoundError("Directory not found: /missing/")

        args = SendFileContentArgs(path="/missing/file.txt", content="")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "not found" in result.error.lower()
        assert result.error_type == "file_not_found"


class TestPermissionDeniedErrors:
    """Tests for permission denied error scenarios."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_permission_denied_error_handling(self, mock_send):
        """Should handle permission denied with clear error message."""
        mock_send.side_effect = PermissionError("Permission denied: /etc/passwd")

        args = SendFileContentArgs(path="/etc/passwd", content="")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "permission denied" in result.error.lower()
        assert "/etc/passwd" in result.error
        assert result.error_type == "permission_denied"

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_security_violation_error_handling(self, mock_send):
        """Should handle security violations with clear error message."""
        mock_send.side_effect = SecurityError("Path outside allowed directories: /etc/passwd")

        args = SendFileContentArgs(path="/etc/passwd", content="")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "security" in result.error.lower()
        assert "not allowed" in result.error.lower()
        assert result.error_type == "security_violation"


class TestSamplingRequestErrors:
    """Tests for sampling request failure scenarios."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_sampling_request_failure(self, mock_send):
        """Should handle sampling request failures gracefully."""
        mock_send.side_effect = ConnectionError("MCP sampling request failed")

        args = SendFileContentArgs(path="/docs/file.txt", content="")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "communication error" in result.error.lower()
        assert result.error_type == "sampling_failure"

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_unsupported_client_fallback(self, mock_send):
        """Should provide fallback for unsupported MCP clients."""
        mock_send.side_effect = NotImplementedError("Sampling not supported")

        args = SendFileContentArgs(path="/docs/file.txt", content="")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "not supported" in result.error.lower()
        assert result.error_type == "unsupported_operation"
        assert "upgrade" in result.instruction.lower()


class TestCacheErrors:
    """Tests for cache error scenarios."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_cache_write_failure(self, mock_send):
        """Should handle cache write failures gracefully."""
        mock_send.side_effect = OSError("Disk full")

        args = SendFileContentArgs(path="/docs/file.txt", content="test content")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "cache error" in result.error.lower()
        assert result.error_type == "cache_failure"

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_memory_error_handling(self, mock_send):
        """Should handle memory errors for large files."""
        mock_send.side_effect = MemoryError("File too large")

        args = SendFileContentArgs(path="/docs/huge_file.txt", content="x" * 1000000)

        result = await internal_send_file_content(args)

        assert result.success is False
        assert "memory" in result.error.lower()
        assert result.error_type == "resource_exhausted"
