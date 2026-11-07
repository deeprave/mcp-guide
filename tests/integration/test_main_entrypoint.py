"""CLI process-level integration coverage."""

import socket
import subprocess
import sys

import pytest


@pytest.mark.slow
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
