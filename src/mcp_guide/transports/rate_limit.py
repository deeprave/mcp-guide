"""HTTP-only ASGI request-rate limiting."""

import asyncio
import math
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

from mcp_guide.content_limits import ContentLimits

WINDOW_SECONDS = 15.0

AsgiApp = Callable[
    [dict[str, Any], Callable[[], Awaitable[dict[str, Any]]], Callable[[dict[str, Any]], Awaitable[None]]],
    Awaitable[None],
]


class HttpRateLimitMiddleware:
    """Apply process and established-session request limits before MCP handling."""

    def __init__(
        self,
        application: AsgiApp,
        limits: ContentLimits,
        *,
        session_is_established: Callable[[str], bool] | None = None,
    ) -> None:
        self._application = application
        self._limits = limits
        self._session_is_established = session_is_established or (lambda _session_id: True)
        self._service_requests: deque[float] = deque()
        self._session_requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    @staticmethod
    def _session_id(scope: dict[str, Any]) -> str | None:
        for name, value in scope.get("headers", []):
            if name.lower() == b"mcp-session-id":
                return value.decode("utf-8", errors="ignore") or None
        return None

    @staticmethod
    def _trim(requests: deque[float], now: float) -> None:
        while requests and requests[0] <= now - WINDOW_SECONDS:
            requests.popleft()

    def _trim_session_requests(self, now: float) -> None:
        """Drop expired counters so departed or unknown clients retain no state."""
        for session_id, requests in list(self._session_requests.items()):
            self._trim(requests, now)
            if not requests:
                del self._session_requests[session_id]

    async def _admit(self, session_id: str | None) -> tuple[int | None, int | None]:
        now = monotonic()
        async with self._lock:
            self._trim(self._service_requests, now)
            self._trim_session_requests(now)
            service_capacity = self._limits.http_service_rate_limit * int(WINDOW_SECONDS)
            if len(self._service_requests) >= service_capacity:
                return 503, math.ceil(self._service_requests[0] + WINDOW_SECONDS - now)
            if session_id is not None and self._session_is_established(session_id):
                requests = self._session_requests[session_id]
                self._trim(requests, now)
                session_capacity = self._limits.http_session_rate_limit * int(WINDOW_SECONDS)
                if len(requests) >= session_capacity:
                    return 429, math.ceil(requests[0] + WINDOW_SECONDS - now)
                requests.append(now)
            self._service_requests.append(now)
        return None, None

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope.get("type") != "http":
            await self._application(scope, receive, send)
            return
        status, retry_after = await self._admit(self._session_id(scope))
        if status is None:
            await self._application(scope, receive, send)
            return
        body = b"Too Many Requests" if status == 429 else b"Service Unavailable"
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [(b"retry-after", str(max(1, retry_after or 1)).encode())],
            }
        )
        await send({"type": "http.response.body", "body": body})
