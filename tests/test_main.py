"""CLI errors produce observable logs and the correct process exit."""

import logging
import socket
import subprocess
import sys

import click
import pytest

from mcp_guide.cli import ServerConfig
from mcp_guide.main import _handle_cli_error


def test_no_cli_error_continues_silently(caplog):
    with caplog.at_level(logging.INFO, logger="mcp_guide.main"):
        _handle_cli_error(ServerConfig(cli_error=None, should_exit=False))
    assert caplog.records == []


def test_ctrl_c_logs_interruption_and_exits_130(caplog):
    with caplog.at_level(logging.INFO, logger="mcp_guide.main"):
        with pytest.raises(SystemExit) as error:
            _handle_cli_error(ServerConfig(cli_error=KeyboardInterrupt("Ctrl+C"), should_exit=True))
    assert error.value.code == 130
    assert caplog.messages == ["Interrupted by user (Ctrl+C)"]


def test_cli_error_logs_reason_and_continues_with_defaults(caplog):
    with caplog.at_level(logging.INFO, logger="mcp_guide.main"):
        _handle_cli_error(ServerConfig(cli_error=click.UsageError("Invalid option"), should_exit=False))
    assert [(record.levelname, record.message) for record in caplog.records] == [
        ("ERROR", "CLI error: Invalid option"),
        ("WARNING", "Continuing with default configuration due to CLI error"),
    ]


def test_occupied_dual_stack_endpoint_exits_without_traceback(tmp_path):
    if not socket.has_dualstack_ipv6():
        pytest.skip("Host does not support dual-stack TCP listeners")
    with socket.create_server(("::", 0), family=socket.AF_INET6, dualstack_ipv6=True) as occupied:
        endpoint = f"http://[::]:{occupied.getsockname()[1]}"
        result = subprocess.run(
            [sys.executable, "-m", "mcp_guide.main", endpoint, "--configdir", str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    assert result.returncode == 1
    assert endpoint in result.stderr
    assert "already in use" in result.stderr
    assert "different port" in result.stderr
    assert "Traceback" not in result.stderr
