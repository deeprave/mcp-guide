"""MCP context data structures and management."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urlparse

from mcp_guide.core.mcp_log import get_logger

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

if TYPE_CHECKING:
    from mcp_guide.agent_detection import AgentInfo

logger = get_logger(__name__)


# Bootstrap cache for MCP data extracted before session exists.
# Consumed by get_or_create_session after session creation.
_bootstrap_roots: list[Any] = []
_bootstrap_agent_info: Optional["AgentInfo"] = None
_bootstrap_client_params: Optional[dict[str, Any]] = None


async def cache_mcp_globals(ctx: Optional["Context"] = None) -> bool:  # type: ignore[type-arg]
    """Cache MCP globals (roots, agent info, client params) if context available.

    Writes to the current session if one exists, otherwise stores in module-level
    bootstrap variables for transfer to session after creation.

    Args:
        ctx: Optional MCP Context (FastMCP auto-injects in tools)

    Returns:
        True if context was available and cached, False otherwise
    """
    global _bootstrap_roots, _bootstrap_agent_info, _bootstrap_client_params

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
                logger.debug(f"Agent detection failed: {agent_e}")

        # Try to extract roots (this may fail for CLI agents)
        try:
            if hasattr(ctx, "session") and hasattr(ctx.session, "list_roots"):
                roots_result = await ctx.session.list_roots()
                if roots_result.roots:
                    roots = list(roots_result.roots)
        except Exception as roots_e:
            logger.debug(f"Failed to get roots (expected for CLI agents): {roots_e}")

    except AttributeError:
        # Client doesn't support basic context - try to get just agent info
        try:
            if hasattr(ctx, "session") and hasattr(ctx.session, "client_params") and ctx.session.client_params:
                client_params = ctx.session.client_params
                agent_info = detect_agent(client_params)
        except Exception:
            return False
    except Exception as e:
        logger.debug(f"Failed to cache MCP globals: {e}")
        return False

    # Write to session if one exists, otherwise bootstrap cache
    from mcp_guide.session import get_active_session

    session = get_active_session()
    if session is not None:
        session.roots = roots
        session.agent_info = agent_info
        session.client_params = client_params
    else:
        _bootstrap_roots = roots
        _bootstrap_agent_info = agent_info
        _bootstrap_client_params = client_params

    return True


def consume_bootstrap_mcp_data() -> tuple[list[Any], Optional["AgentInfo"], Optional[dict[str, Any]]]:
    """Consume bootstrap MCP data and clear it. Called after session creation."""
    global _bootstrap_roots, _bootstrap_agent_info, _bootstrap_client_params
    data = (_bootstrap_roots, _bootstrap_agent_info, _bootstrap_client_params)
    _bootstrap_roots = []
    _bootstrap_agent_info = None
    _bootstrap_client_params = None
    return data


def _get_roots() -> list[Any]:
    """Get roots from session if available, otherwise from bootstrap cache."""
    from mcp_guide.session import get_active_session

    session = get_active_session()
    if session is not None and session.roots:
        return session.roots
    return _bootstrap_roots


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
