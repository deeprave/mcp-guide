"""Tests for command security validation and error handling."""

from unittest.mock import AsyncMock, patch

import pytest

from tests.helpers import create_unbound_test_session, request_context_for


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


@pytest.mark.anyio
async def test_command_permission_failure_returns_a_clear_error(runtime, tmp_path):
    import yaml

    from mcp_guide.prompts.guide_prompt import handle_command

    commands = tmp_path / "_commands"
    commands.mkdir()
    (commands / "restricted.mustache").write_text("Restricted content")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = create_unbound_test_session(runtime)
    # Inject the permission failure at the rendering boundary; discovery and context remain real.
    with patch(
        "mcp_guide.prompts.guide_prompt.render_template",
        new=AsyncMock(side_effect=PermissionError("Permission denied")),
    ):
        result = await handle_command("restricted", request_context=await request_context_for(session), middleware=[])
    assert not result.success
    assert "permission" in result.error.lower()
