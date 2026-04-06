"""Tests for command security validation and error handling."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCommandSecurity:
    """Test command security validation."""

    @pytest.mark.parametrize(
        "dangerous_command",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "./../../secret",
            "../config",
            "subdir/../../../etc/hosts",
            "/usr/bin/ls",
            "/home/user/.ssh/id_rsa",
            "C:\\Windows\\System32\\cmd.exe",
            "/var/log/auth.log",
            "command\x00",
            "command\n",
            "command\r",
            "command\t",
            "command;rm -rf /",
            "command|cat /etc/passwd",
            "command`whoami`",
            "command$(id)",
        ],
    )
    def test_invalid_command_paths_rejected(self, dangerous_command: str) -> None:
        """Dangerous command paths should fail validation."""
        from mcp_guide.commands.security import validate_command_path_full

        error, _sanitized = validate_command_path_full(dangerous_command)

        assert error is not None

    @pytest.mark.parametrize(
        "valid_command",
        [
            "help",
            "status",
            "create/collection",
            "list/categories",
            "info/project",
            "command-with-dashes",
            "command_with_underscores",
            "command123",
            "nested/deep/command",
        ],
    )
    def test_valid_command_names_allowed(self, valid_command: str) -> None:
        """Valid command names should pass security validation."""
        from mcp_guide.commands.security import validate_command_path_full

        error, sanitized = validate_command_path_full(valid_command)

        assert error is None
        assert sanitized == valid_command


class TestCommandErrorHandling:
    """Test comprehensive error handling."""

    @pytest.mark.anyio
    async def test_file_permission_errors(self, tmp_path) -> None:
        """Should handle file permission errors gracefully."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.discovery.files import FileInfo
        from mcp_guide.result import Result
        from mcp_guide.server import create_server

        create_server(ServerConfig())
        from mcp_guide.prompts.guide_prompt import handle_command
        from mcp_guide.render.context import TemplateContext

        mock_ctx = SimpleNamespace(session=SimpleNamespace(project_root=str(tmp_path)))
        commands_dir = tmp_path / "_commands"
        commands_dir.mkdir()
        command_file = commands_dir / "restricted.mustache"
        command_file.write_text(
            """---
type: guide-command
description: Restricted command
---
Restricted
"""
        )
        file_info = FileInfo(
            path=Path("restricted.mustache"),
            size=100,
            content_size=100,
            mtime=1234567890,
            name="restricted.mustache",
            ctime=1234567890,
        )

        with (
            patch("mcp_guide.prompts.guide_prompt.get_session", new=AsyncMock()) as mock_session,
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch("mcp_guide.prompts.guide_prompt.resolve_all_flags", new=AsyncMock(return_value={})),
            patch("mcp_guide.prompts.guide_prompt._is_help_command", new=AsyncMock(return_value=False)),
            patch("mcp_guide.prompts.guide_prompt.discover_commands", new=AsyncMock(return_value=[])),
            patch(
                "mcp_guide.prompts.guide_prompt._discover_command_file",
                new=AsyncMock(return_value=Result.ok(file_info)),
            ),
            patch("mcp_guide.prompts.guide_prompt.logger.exception"),
            patch("mcp_guide.prompts.guide_prompt.render_template", side_effect=PermissionError("Permission denied")),
        ):
            mock_session_obj = AsyncMock()
            mock_session_obj.get_docroot = AsyncMock(return_value=str(tmp_path))
            mock_session.return_value = mock_session_obj

            mock_base_context = TemplateContext({})
            mock_context.return_value = mock_base_context

            result = await handle_command("restricted", ctx=mock_ctx, middleware=[])

            assert result.success is False
            assert result.error is not None
            assert "permission" in result.error.lower()

    @pytest.mark.anyio
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
