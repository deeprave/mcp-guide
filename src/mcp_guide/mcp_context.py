"""MCP context data structures and management."""

from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urlparse

from mcp_guide.core.mcp_log import get_logger

try:
    from fastmcp import Context
except ImportError:
    Context = None  # ty: ignore[invalid-assignment]
if TYPE_CHECKING:
    from mcp_guide.agent_detection import AgentInfo

logger = get_logger(__name__)


# Bootstrap cache for MCP data extracted before session exists.
# Uses ContextVar for per-task isolation (safe under HTTP transport with concurrent clients).
# Consumed by get_or_create_session after session creation.
_bootstrap_roots: ContextVar[list[Any]] = ContextVar("_bootstrap_roots", default=[])
_bootstrap_agent_info: ContextVar[Optional["AgentInfo"]] = ContextVar("_bootstrap_agent_info", default=None)
_bootstrap_client_params: ContextVar[Optional[dict[str, Any]]] = ContextVar("_bootstrap_client_params", default=None)


async def cache_mcp_globals(ctx: Optional["Context"] = None) -> bool:
    """Cache MCP globals (roots, agent info, client params) if context available.

    Writes to the current session if one exists, otherwise stores in module-level
    bootstrap variables for transfer to session after creation.

    Args:
        ctx: Optional MCP Context (FastMCP auto-injects in tools)

    Returns:
        True if context was available and cached, False otherwise
    """
    if ctx is None:
        return False

    from mcp_guide.agent_detection import detect_agent

    roots: list[Any] = []
    agent_info = None
    client_params = None

    try:
        # Extract client params - try both paths
        if hasattr(ctx, "session") and hasattr(ctx.session, "client_params") and ctx.session.client_params:
            client_params = ctx.session.client_params
        elif hasattr(ctx, "client_params") and ctx.client_params:
            client_params = ctx.client_params

        # Try to detect agent info from client params
        if client_params:
            try:
                agent_info = detect_agent(client_params)
                logger.debug(f"Agent info detected: {agent_info.name if agent_info else 'None'}")
            except Exception as agent_e:
                logger.error(f"Agent detection failed: {agent_e}", exc_info=True)

        # Try to extract roots (this may fail for CLI agents)
        try:
            if hasattr(ctx, "session") and hasattr(ctx.session, "list_roots"):
                roots_result = await ctx.session.list_roots()
                if roots_result.roots:
                    roots = list(roots_result.roots)
        except Exception as roots_e:
            logger.debug(f"Failed to get roots (expected for CLI agents): {roots_e}")

    except AttributeError as e:
        # Client doesn't support basic context - try to get just agent info
        logger.warning(f"Client context attribute error, attempting fallback: {e}")
        try:
            if hasattr(ctx, "session") and hasattr(ctx.session, "client_params") and ctx.session.client_params:
                client_params = ctx.session.client_params
                agent_info = detect_agent(client_params)
        except Exception as fallback_e:
            logger.error(f"Fallback agent detection failed: {fallback_e}", exc_info=True)
            return False
    except Exception as e:
        logger.error(f"Failed to cache MCP globals: {e}", exc_info=True)
        return False

    # Write to session if one exists, otherwise bootstrap cache
    from mcp_guide.session import get_active_session

    session = get_active_session()
    if session is not None:
        from pydantic import BaseModel

        normalized_params = client_params.model_dump() if isinstance(client_params, BaseModel) else client_params

        # Only invalidate template context cache if MCP globals actually changed
        changed = (
            getattr(session, "roots", None) != roots
            or getattr(session, "agent_info", None) != agent_info
            or getattr(session, "client_params", None) != normalized_params
        )

        session.roots = roots
        session.agent_info = agent_info
        session.client_params = normalized_params  # ty: ignore[invalid-assignment]

        if changed:
            from mcp_guide.render.cache import invalidate_template_context_cache

            invalidate_template_context_cache()
    else:
        _bootstrap_roots.set(roots)
        _bootstrap_agent_info.set(agent_info)
        _bootstrap_client_params.set(client_params)  # ty: ignore[invalid-argument-type]

    return True


def consume_bootstrap_mcp_data() -> tuple[list[Any], Optional["AgentInfo"], Optional[dict[str, Any]]]:
    """Consume bootstrap MCP data and clear it. Called after session creation."""
    data = (_bootstrap_roots.get(), _bootstrap_agent_info.get(), _bootstrap_client_params.get())
    _bootstrap_roots.set([])
    _bootstrap_agent_info.set(None)
    _bootstrap_client_params.set(None)
    return data


def _get_roots() -> list[Any]:
    """Get roots from session if available, otherwise from bootstrap cache."""
    from mcp_guide.session import get_active_session

    session = get_active_session()
    if session is not None:
        return session.roots
    return _bootstrap_roots.get()


async def resolve_project_name() -> str:
    """Resolve project name from roots or environment fallbacks.

    Resolution priority:
    1. Client roots (session or bootstrap) - PRIMARY
    2. PWD environment variable - FALLBACK

    Returns:
        Project name string

    Raises:
        ValueError: If no project context is available
    """
    import os

    roots = _get_roots()
    if roots:
        first_root = roots[0]
        if str(first_root.uri).startswith("file://"):
            parsed = urlparse(str(first_root.uri))
            project_name = Path(parsed.path).name
            if project_name:
                return project_name

    # Fallback: PWD environment variable
    pwd = os.environ.get("PWD")
    if pwd and Path(pwd).is_absolute():
        return Path(pwd).name

    raise ValueError("Project context not available. Call set_project() with the basename of your current directory.")


async def resolve_project_path() -> Path:
    """Resolve full project path for hash calculation.

    Returns:
        Full absolute project path as Path object

    Raises:
        ValueError: If no project context is available
    """
    import os

    roots = _get_roots()
    if roots:
        first_root = roots[0]
        if str(first_root.uri).startswith("file://"):
            parsed = urlparse(str(first_root.uri))
            return Path(parsed.path).resolve()

    # Fallback: PWD environment variable
    pwd = os.environ.get("PWD")
    if pwd and Path(pwd).is_absolute():
        return Path(pwd).resolve()

    raise ValueError("Project context not available. Cannot determine project path.")
