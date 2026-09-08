"""Behaviour tests for the HTTP request-rate ASGI boundary."""

import pytest

from mcp_guide.content_limits import ContentLimits
from mcp_guide.transports.rate_limit import HttpRateLimitMiddleware


async def _request(app, *, session_id: str | None = None):
    messages = []
    headers = [] if session_id is None else [(b"mcp-session-id", session_id.encode())]

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app({"type": "http", "headers": headers}, receive, send)
    return messages


@pytest.mark.anyio
async def test_session_rate_limit_rejects_before_calling_application():
    calls = 0

    async def application(scope, receive, send):
        nonlocal calls
        calls += 1
        await send({"type": "http.response.start", "status": 200, "headers": []})

    app = HttpRateLimitMiddleware(application, ContentLimits(http_session_rate_limit=1, http_service_rate_limit=100))
    for _ in range(15):
        assert (await _request(app, session_id="one"))[0]["status"] == 200
    response = await _request(app, session_id="one")
    assert response[0]["status"] == 429
    assert calls == 15


@pytest.mark.anyio
async def test_service_rate_limit_applies_before_session_establishment():
    async def application(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})

    app = HttpRateLimitMiddleware(application, ContentLimits(http_session_rate_limit=100, http_service_rate_limit=1))
    for _ in range(15):
        assert (await _request(app))[0]["status"] == 200
    assert (await _request(app))[0]["status"] == 503


@pytest.mark.anyio
async def test_unknown_session_header_uses_only_the_service_budget():
    async def application(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})

    app = HttpRateLimitMiddleware(
        application,
        ContentLimits(http_session_rate_limit=1, http_service_rate_limit=100),
        session_is_established=lambda _session_id: False,
    )
    for _ in range(16):
        assert (await _request(app, session_id="unknown"))[0]["status"] == 200
    assert app._session_requests == {}
