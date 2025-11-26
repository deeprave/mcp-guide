"""Integration tests for server startup."""

import asyncio
import json
import subprocess
from typing import AsyncIterator

import pytest


@pytest.fixture
async def server_process() -> AsyncIterator[subprocess.Popen]:
    """Start the MCP server process."""
    process = subprocess.Popen(
        ["uv", "run", "mcp-guide"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    yield process

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


async def wait_for_server_ready(process: subprocess.Popen, timeout: float = 2.0) -> bool:
    """Poll server until ready or timeout."""
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if process.poll() is not None:
            return False
        await asyncio.sleep(0.1)
    return process.poll() is None


async def read_response_with_timeout(process: subprocess.Popen, timeout: float = 2.0) -> str | None:
    """Read response from server with timeout using polling."""
    assert process.stdout is not None
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if process.stdout.readable():
            if line := process.stdout.readline():
                return line
        await asyncio.sleep(0.1)
    return None


@pytest.mark.asyncio
async def test_server_starts_without_errors(server_process: subprocess.Popen) -> None:
    """Test that server process starts without immediate errors."""
    ready = await wait_for_server_ready(server_process)

    if not ready:
        server_process.poll()
        returncode = server_process.returncode

        stderr_output = None
        if server_process.stderr is not None:
            try:
                stderr_output = server_process.stderr.read()
            except Exception as exc:
                stderr_output = f"<failed to read stderr: {exc!r}>"

        pytest.fail(
            f"Server process failed to start.\nready={ready}\nreturncode={returncode}\nstderr:\n{stderr_output}"
        )


@pytest.mark.asyncio
async def test_server_responds_to_initialize(server_process: subprocess.Popen) -> None:
    """Test that server responds to MCP initialize request."""
    ready = await wait_for_server_ready(server_process)
    assert ready, "Server not ready"

    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    assert server_process.stdin is not None
    server_process.stdin.write(json.dumps(initialize_request) + "\n")
    server_process.stdin.flush()

    response_line = await read_response_with_timeout(server_process)
    assert response_line, "No response from server"

    response = json.loads(response_line)
    assert "result" in response or "error" in response
    assert response.get("id") == 1


@pytest.mark.asyncio
async def test_server_advertises_correct_name(server_process: subprocess.Popen) -> None:
    """Test that server advertises correct server name."""
    ready = await wait_for_server_ready(server_process)
    assert ready, "Server not ready"

    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    assert server_process.stdin is not None
    server_process.stdin.write(json.dumps(initialize_request) + "\n")
    server_process.stdin.flush()

    response_line = await read_response_with_timeout(server_process)
    assert response_line, "No response from server"

    response = json.loads(response_line)

    if "error" in response:
        pytest.fail(f"Server returned error: {response['error']}")

    assert "result" in response, "Response missing 'result' field"
    server_info = response["result"].get("serverInfo", {})
    assert server_info.get("name") == "mcp-guide"
