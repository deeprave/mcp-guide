"""Dual-stack startup failures and cancellation release their actual bind."""

import asyncio
import errno
import socket

import pytest
from fastmcp import FastMCP

from mcp_guide.transports.http import HttpTransport


@pytest.mark.anyio
@pytest.mark.parametrize("error_number", [errno.EACCES, errno.EAFNOSUPPORT])
async def test_dual_stack_bind_failure_identifies_endpoint(error_number, monkeypatch):
    monkeypatch.setattr(socket, "has_dualstack_ipv6", lambda: True)

    def fail_bind(*args, **kwargs):
        raise OSError(error_number, "Synthetic bind failure")

    monkeypatch.setattr(socket, "create_server", fail_bind)
    transport = HttpTransport("http", "::", 8080, FastMCP())
    try:
        with pytest.raises(RuntimeError) as error:
            await transport.start()
        assert "http://[::]:8080" in str(error.value)
        assert "Synthetic bind failure" in str(error.value)
        assert isinstance(error.value.__cause__, OSError)
        assert transport.server_task is None
    finally:
        await transport.stop()


@pytest.mark.anyio
async def test_unsupported_dual_stack_fails_startup(monkeypatch):
    monkeypatch.setattr(socket, "has_dualstack_ipv6", lambda: False)
    transport = HttpTransport("http", "::", 8080, FastMCP())
    try:
        with pytest.raises(RuntimeError, match="[Dd]ual-stack"):
            await transport.start()
        assert transport.server_task is None
    finally:
        await transport.stop()


@pytest.mark.anyio
async def test_occupied_dual_stack_bind_fails_startup():
    if not socket.has_dualstack_ipv6():
        pytest.skip("Host does not support dual-stack TCP listeners")
    with socket.create_server(("::", 0), family=socket.AF_INET6, dualstack_ipv6=True) as occupied:
        transport = HttpTransport("http", "::", occupied.getsockname()[1], FastMCP())
        try:
            with pytest.raises(RuntimeError, match="already in use"):
                await transport.start()
            assert transport.server_task is None
        finally:
            await transport.stop()


@pytest.mark.anyio
@pytest.mark.parametrize("exit_mode", ["failure", "cancellation"])
async def test_serving_exit_releases_dual_stack_bind(exit_mode, monkeypatch):
    if not socket.has_dualstack_ipv6():
        pytest.skip("Host does not support dual-stack TCP listeners")
    with socket.create_server(("::", 0), family=socket.AF_INET6, dualstack_ipv6=True) as reservation:
        port = reservation.getsockname()[1]
    entered = asyncio.Event()
    release = asyncio.Event()

    async def fail_serve(self, sockets=None):
        entered.set()
        await release.wait()
        raise RuntimeError("Synthetic serving startup failure")

    monkeypatch.setattr("uvicorn.Server.serve", fail_serve)
    transport = HttpTransport("http", "::", port, FastMCP())
    await transport.start()
    try:
        await entered.wait()
        # The transport must already own the requested bind during ASGI startup.
        with pytest.raises(OSError):
            with socket.create_server(("::", port), family=socket.AF_INET6, dualstack_ipv6=True):
                pass
        if exit_mode == "cancellation":
            transport.server_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await transport.server_task
        else:
            release.set()
            with pytest.raises(RuntimeError, match="Synthetic"):
                await transport.server_task
        # Release must not depend on a later stop() call.
        with socket.create_server(("::", port), family=socket.AF_INET6, dualstack_ipv6=True):
            pass
    finally:
        release.set()
        try:
            await transport.stop()
        except asyncio.CancelledError:
            pass
