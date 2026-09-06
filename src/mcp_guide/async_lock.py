"""Async synchronisation primitives for runtime lifecycle coordination."""

import asyncio
from typing import Any


class AsyncReentrantLock:
    """An ``asyncio`` lock that may be reacquired by its owning task."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._owner: asyncio.Task[Any] | None = None
        self._depth = 0

    async def __aenter__(self) -> "AsyncReentrantLock":
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("AsyncReentrantLock requires an asyncio task")
        if self._owner is task:
            self._depth += 1
            return self

        await self._lock.acquire()
        self._owner = task
        self._depth = 1
        return self

    async def __aexit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        task = asyncio.current_task()
        if self._owner is not task:
            raise RuntimeError("AsyncReentrantLock may only be released by its owning task")

        self._depth -= 1
        if self._depth == 0:
            self._owner = None
            self._lock.release()
