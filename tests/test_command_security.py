"""Tests for command security validation and error handling."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCommandSecurity:
    """Test command security validation."""

    @pytest.mark.asyncio
    async def test_directory_traversal_prevention(self, guide_function) -> None:
        """Should prevent directory traversal attacks."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        # Test various directory traversal attempts
        dangerous_commands = [
            ":../../../etc/passwd",
            ":..\\..\\..\\windows\\system32\\config\\sam",
            ":/etc/passwd",
            ":./../../secret",
            ":../config",
            ":subdir/../../../etc/hosts",
        ]

        for dangerous_cmd in dangerous_commands:
            result_str = await guide_function(dangerous_cmd, ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "security" in result["error"].lower() or "invalid" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_absolute_path_prevention(self, guide_function) -> None:
        """Should prevent absolute path commands."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        dangerous_commands = [
            ":/usr/bin/ls",
            ":/home/user/.ssh/id_rsa",
            ":C:\\Windows\\System32\\cmd.exe",
            ":/var/log/auth.log",
        ]

        for dangerous_cmd in dangerous_commands:
            result_str = await guide_function(dangerous_cmd, ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "security" in result["error"].lower() or "invalid" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_special_character_validation(self, guide_function) -> None:
        """Should reject commands with dangerous special characters."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        dangerous_commands = [
            ":command\x00",  # Null byte
            ":command\n",  # Newline
            ":command\r",  # Carriage return
            ":command\t",  # Tab
            ":command;rm -rf /",  # Command injection attempt
            ":command|cat /etc/passwd",  # Pipe injection
            ":command`whoami`",  # Backtick injection
            ":command$(id)",  # Command substitution
        ]

        for dangerous_cmd in dangerous_commands:
            result_str = await guide_function(dangerous_cmd, ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "security" in result["error"].lower() or "invalid" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_valid_command_names_allowed(self, guide_function) -> None:
        """Should allow valid command names."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        # Mock the command handler to return success for valid commands
        with patch("mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock()) as mock_handle:
            from mcp_guide.result import Result

            mock_handle.return_value = Result.ok("Command executed")

            valid_commands = [
                ":help",
                ":status",
                ":create/collection",
                ":list/categories",
                ":info/project",
                ":command-with-dashes",
                ":command_with_underscores",
                ":command123",
                ":nested/deep/command",
            ]

            for valid_cmd in valid_commands:
                result_str = await guide_function(valid_cmd, ctx=mock_ctx)
                result = json.loads(result_str)

                # Should not be rejected for security reasons
                if not result["success"]:
                    assert "security" not in result["error"].lower()


class TestCommandErrorHandling:
    """Test comprehensive error handling."""

    @pytest.mark.asyncio
    async def test_missing_command_file(self, guide_function) -> None:
        """Should handle missing command files with helpful error."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"
        mock_ctx.session.get_docroot.return_value = "/test/project"

        # Mock directory exists but empty command discovery (command not found)
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("mcp_guide.utils.command_discovery.discover_commands", new=AsyncMock(return_value=[])),
        ):
            result_str = await guide_function(":nonexistent", ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "not found" in result["error"].lower()
            assert "nonexistent" in result["error"]

    @pytest.mark.asyncio
    async def test_template_rendering_errors(self, guide_function) -> None:
        """Should handle template rendering errors gracefully."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"
        mock_ctx.session.get_docroot.return_value = "/test/project"

        # Mock directory exists, command discovery dependencies, template context, and template rendering failure
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("mcp_guide.session.get_or_create_session", new=AsyncMock()) as mock_session,
            patch("mcp_guide.models.resolve_all_flags", new=AsyncMock()) as mock_resolve_flags,
            patch("mcp_guide.utils.command_discovery.discover_command_files", new=AsyncMock()) as mock_discover_files,
            patch("mcp_guide.prompts.guide_prompt.discover_category_files", new=AsyncMock()) as mock_files,
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch(
                "mcp_guide.utils.template_context_cache.get_template_contexts", new=AsyncMock()
            ) as mock_discover_context,
            patch("mcp_guide.prompts.guide_prompt.render_template", new=AsyncMock()) as mock_render,
            patch("aiofiles.open") as mock_aiofiles,
        ):
            # Mock session methods
            mock_session_obj = AsyncMock()
            mock_session_obj.get_project = AsyncMock()
            mock_session_obj.get_docroot = AsyncMock(return_value="/test/project")
            mock_session.return_value = mock_session_obj
            mock_resolve_flags.return_value = {}
            mock_session.return_value = mock_session_obj
            from mcp_guide.utils.file_discovery import FileInfo
            from mcp_guide.utils.template_context import TemplateContext

            # Mock command file discovery to return a file
            mock_discover_files.return_value = [
                FileInfo(
                    path=Path("broken.mustache"),
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="broken.mustache",
                    content="",
                    category="",
                    collection="",
                    ctime=1234567890,
                )
            ]

            # Mock file discovery to return a file (for content retrieval)
            mock_files.return_value = [
                FileInfo(
                    path=Path("broken.mustache"),
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="broken.mustache",
                    content="",
                    category="",
                    collection="",
                    ctime=1234567890,
                )
            ]

            # Mock template context
            mock_base_context = TemplateContext({})
            mock_context.return_value = mock_base_context
            mock_discover_context.return_value = mock_base_context

            # Mock render_template to raise exception (new API behavior)
            mock_render.side_effect = RuntimeError("Invalid template syntax")

            # Create proper async context manager mock for file reading
            class MockAsyncFile:
                async def read(self):
                    return "{{invalid template}}"

                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_aiofiles.return_value = MockAsyncFile()

            result_str = await guide_function(":broken", ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "template" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_file_permission_errors(self, guide_function) -> None:
        """Should handle file permission errors gracefully."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        # Mock directory exists, command discovery, template context, and file discovery to return a file, but file reading to fail
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("mcp_guide.session.get_or_create_session", new=AsyncMock()) as mock_session,
            patch("mcp_guide.models.resolve_all_flags", new=AsyncMock()) as mock_resolve_flags,
            patch("mcp_guide.prompts.guide_prompt.discover_commands", new=AsyncMock(return_value=[])),
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch("mcp_guide.prompts.guide_prompt.discover_category_files", new=AsyncMock()) as mock_discover,
        ):
            # Mock session methods
            mock_session_obj = AsyncMock()
            mock_session_obj.get_project = AsyncMock()
            mock_session_obj.get_docroot = AsyncMock(return_value="/test/project")
            mock_session.return_value = mock_session_obj
            mock_resolve_flags.return_value = {}
            from mcp_guide.utils.file_discovery import FileInfo
            from mcp_guide.utils.template_context import TemplateContext

            # Mock template context
            mock_base_context = TemplateContext({})
            mock_context.return_value = mock_base_context

            mock_discover.return_value = [
                FileInfo(
                    path=Path("restricted.mustache"),
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="restricted.mustache",
                    category="",
                    collection="",
                    ctime=1234567890,
                )
            ]

            # Mock file reading to raise permission error
            with patch("mcp_guide.core.file_reader.aiofiles.open", side_effect=PermissionError("Permission denied")):
                result_str = await guide_function(":restricted", ctx=mock_ctx)
                result = json.loads(result_str)

                assert result["success"] is False
                assert "error reading" in result["error"].lower() or "permission" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_malformed_argument_edge_cases(self, guide_function) -> None:
        """Should handle malformed arguments gracefully."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        # Test malformed arguments that pass security validation but fail parsing
        # Use simple command names without special characters
        malformed_commands = [
            ":help --",  # Empty flag
        ]

        # Mock directory exists and command discovery for these tests
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("mcp_guide.prompts.guide_prompt.discover_commands", new=AsyncMock(return_value=[])),
        ):
            for malformed_cmd in malformed_commands:
                result_str = await guide_function(malformed_cmd, ctx=mock_ctx)
                result = json.loads(result_str)

                # Should either succeed (if parser handles it) or fail with clear error
                if not result["success"]:
                    # Accept various error types since the command might not be found
                    assert any(
                        keyword in result["error"].lower()
                        for keyword in ["parsing", "argument", "not found", "invalid"]
                    )
