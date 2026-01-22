"""Integration tests for logging functionality using MCP SDK client."""

import os
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_server_starts_with_trace_logging(tmp_path: Path) -> None:
    """Test server starts successfully with TRACE logging enabled."""
    log_file = tmp_path / "test.log"

    # Create config to skip first-run installation
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "installer.yaml").write_text("docroot: /tmp/test\n")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-guide", "--configdir", str(config_dir)],
        env={
            **os.environ,
            "MG_LOG_LEVEL": "TRACE",
            "MG_LOG_FILE": str(log_file),
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.initialize()

            assert result.serverInfo.name == "guide"
            assert log_file.exists(), "Log file should be created"

            log_content = log_file.read_text()
            assert "Starting mcp-guide server" in log_content
            assert "Log level: TRACE" in log_content


@pytest.mark.asyncio
async def test_server_starts_with_json_logging(tmp_path: Path) -> None:
    """Test server starts with JSON logging format."""
    log_file = tmp_path / "test-json.log"

    # Create config to skip first-run installation
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "installer.yaml").write_text("docroot: /tmp/test\n")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-guide", "--configdir", str(config_dir)],
        env={
            **os.environ,
            "MG_LOG_LEVEL": "INFO",
            "MG_LOG_FILE": str(log_file),
            "MG_LOG_JSON": "true",
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.initialize()

            assert result.serverInfo.name == "guide"
            assert log_file.exists(), "Log file should be created"

            log_content = log_file.read_text()
            # JSON logs should contain structured fields
            assert '"level":' in log_content or '"levelname":' in log_content
            assert '"message":' in log_content


@pytest.mark.asyncio
async def test_server_starts_without_logging(tmp_path: Path) -> None:
    """Test server starts successfully without file logging."""
    # Create config to skip first-run installation
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "installer.yaml").write_text("docroot: /tmp/test\n")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-guide", "--configdir", str(config_dir)],
        env={**os.environ, "MG_LOG_LEVEL": "INFO"},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.initialize()
            assert result.serverInfo.name == "guide"


@pytest.mark.asyncio
async def test_log_file_appends_on_multiple_starts(tmp_path: Path) -> None:
    """Test log file is appended to on multiple server starts."""
    log_file = tmp_path / "append-test.log"

    # Create config to skip first-run installation
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "installer.yaml").write_text("docroot: /tmp/test\n")

    # First start
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-guide", "--configdir", str(config_dir)],
        env={
            **os.environ,
            "MG_LOG_LEVEL": "INFO",
            "MG_LOG_FILE": str(log_file),
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

    assert log_file.exists(), "Log file should exist after first start"
    first_size = log_file.stat().st_size
    assert first_size > 0, "Log file should have content after first start"

    # Second start
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

    second_size = log_file.stat().st_size

    assert second_size > first_size, "Log file should grow on second start"
    log_content = log_file.read_text()
    assert log_content.count("Starting mcp-guide server") == 2
