"""MCP context data structures and management."""

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from fastmcp import Context

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.runtime import ClientMetadata, GuideRuntime, OwnerKey, RequestContext

logger = get_logger(__name__)

if TYPE_CHECKING:
    from mcp_guide.session import Session


def extract_client_params(ctx: Any) -> dict[str, Any] | None:
    """Return normalized client information from FastMCP's public context.

    Modern protocol requests carry client information in the reserved request
    metadata field. Retained handshake clients expose the original initialize
    parameters through the public ServerSession property. Guide keeps the same
    ``clientInfo`` mapping internally for agent detection in either case.
    """
    request_context = getattr(ctx, "request_context", None)
    request_meta = request_context.meta if request_context is not None else None
    if isinstance(request_meta, Mapping):
        client_info = request_meta.get("io.modelcontextprotocol/clientInfo")
        if isinstance(client_info, Mapping):
            return {"clientInfo": dict(client_info)}

    session = getattr(ctx, "session", None)
    if session is None:
        return None
    try:
        client_params = session.client_params
    except (AttributeError, RuntimeError):
        return None

    if client_params is None:
        return None
    if hasattr(client_params, "model_dump"):
        return client_params.model_dump(by_alias=True)
    if isinstance(client_params, Mapping):
        return dict(client_params)
    return None


def request_context_from_fastmcp(ctx: Any, *, session_id: str | None = None) -> RequestContext:
    """Adapt public FastMCP request data into Guide's application context.

    Modern requests must provide the session identifier in their tool arguments.
    Retained handshake-era requests use FastMCP's public connection session ID as
    their compatibility owner. An unbound modern request gets an ephemeral owner
    only so callers can report the defined no-project guidance; it is not a
    cross-request Session key.
    """
    request = getattr(ctx, "request_context", None)
    protocol_revision = request.protocol_version if request is not None else "legacy"
    request_id = request.request_id if request is not None else None
    client_params = extract_client_params(ctx) or {}
    client_info = client_params.get("clientInfo")
    if not isinstance(client_info, Mapping):
        client_info = {}
    client = ClientMetadata(name=client_info.get("name"), version=client_info.get("version"))

    if session_id is not None:
        source = "explicit"
        resolved_session_id = session_id
    elif protocol_revision != "2026-07-28":
        source = "legacy"
        resolved_session_id = getattr(ctx, "session_id", None)
    else:
        source = None
        resolved_session_id = None

    if resolved_session_id is not None:
        owner = OwnerKey(resolved_session_id)
    else:
        owner = OwnerKey(f"unbound:{request_id or 'notification'}")

    return RequestContext(
        protocol_revision=protocol_revision,
        request_id=request_id,
        owner=owner,
        client=client,
        session_id=resolved_session_id,
        session_source=source,
    )


def runtime_from_fastmcp(ctx: Any) -> GuideRuntime[Any] | None:
    """Return the Guide runtime carried by FastMCP's public lifespan context."""
    request = getattr(ctx, "request_context", None) if ctx is not None else None
    runtime = request.lifespan_context if request is not None else None
    return runtime if isinstance(runtime, GuideRuntime) else None


def resource_uri_from_fastmcp(ctx: Any | None) -> str | None:
    """Extract a Guide URI through FastMCP's public request wrapper.

    Resource handlers receive URI-template variables separately. Commands also
    need the complete URI so their query arguments can be parsed; keep that
    SDK adaptation here rather than coupling Guide handlers to its shape.
    """
    if ctx is None:
        return None
    request_context = getattr(ctx, "request_context", None)
    request = request_context.request if request_context is not None else None
    params = getattr(request, "params", None)
    uri = getattr(params, "uri", None)
    uri_text = str(uri) if uri is not None else None
    return uri_text if uri_text and uri_text.startswith("guide://") else None


async def cache_mcp_globals(ctx: Optional["Context"], session: "Session") -> bool:
    """Cache MCP agent metadata if context is available.

    Agent metadata belongs to the request-resolved Session. Callers provide that
    Session explicitly; there is no bootstrap or ambient-session lookup that
    could leak metadata across interactions.

    Args:
        ctx: Optional MCP Context (FastMCP auto-injects in tools)
        session: Request-resolved Session that owns the metadata

    Returns:
        True if context was available and cached, False otherwise
    """
    if ctx is None:
        return False

    from mcp_guide.agent_detection import detect_agent

    agent_info = None
    client_params = None

    try:
        client_params = extract_client_params(ctx)

        # Try to detect agent info from client params
        if client_params:
            try:
                agent_info = detect_agent(client_params)
                logger.debug(f"Agent info detected: {agent_info.name if agent_info else 'None'}")
            except Exception as agent_e:
                logger.error(f"Agent detection failed: {agent_e}", exc_info=True)

    except AttributeError as e:
        # Client doesn't support basic context - try to get just agent info
        logger.warning(f"Client context attribute error, attempting fallback: {e}")
        try:
            client_params = extract_client_params(ctx)
            if client_params:
                agent_info = detect_agent(client_params)
        except Exception as fallback_e:
            logger.error(f"Fallback agent detection failed: {fallback_e}", exc_info=True)
            return False
    except Exception as e:
        logger.error(f"Failed to cache MCP globals: {e}", exc_info=True)
        return False

    from pydantic import BaseModel

    normalized_params = client_params.model_dump() if isinstance(client_params, BaseModel) else client_params

    # Only invalidate template context cache if MCP globals actually changed.
    changed = session.agent_info != agent_info or session.client_params != normalized_params

    session.agent_info = agent_info
    session.client_params = normalized_params

    if changed:
        from mcp_guide.render.cache import invalidate_template_context_cache

        invalidate_template_context_cache(session)
    return True


async def resolve_project_path(session: "Session") -> Path:
    """Resolve full project path for hash calculation.

    Returns:
        Full absolute project path as Path object

    Raises:
        ValueError: If no project context is available
    """
    if session.bound_root_path is not None:
        return session.bound_root_path
    raise ValueError("Project context not available. Call set_project(path) with the absolute project root.")
