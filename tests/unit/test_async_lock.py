"""Tests for runtime lifecycle synchronisation."""

import asyncio

import pytest

from mcp_guide.async_lock import AsyncReentrantLock


@pytest.mark.anyio
async def test_async_reentrant_lock_allows_nested_acquisition_by_the_owner() -> None:
    """Nested configuration callbacks may retain the shared gate safely."""
    lock = AsyncReentrantLock()

    async with lock:
        async with lock:
            assert True

    acquired = asyncio.Event()

    async def acquire_from_another_task() -> None:
        async with lock:
            acquired.set()

    await asyncio.create_task(acquire_from_another_task())
    assert acquired.is_set()
