"""Single-thread executor for serialised SQLite operations."""

import asyncio
import concurrent.futures
from collections.abc import Callable
from functools import partial
from typing import Any, TypeVar

T = TypeVar("T")

_executor: concurrent.futures.ThreadPoolExecutor | None = None


def _get_executor() -> concurrent.futures.ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="docstore")
    return _executor


async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a sync callable on the document store thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_get_executor(), partial(func, *args, **kwargs))
