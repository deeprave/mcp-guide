"""MCP context data structures and management."""

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urlparse

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

if TYPE_CHECKING:
    from mcp_guide.agent_detection import AgentInfo

logger = logging.getLogger(__name__)


@dataclass
class CachedMcpContext:
    """Comprehensive MCP context cache."""

    roots: list[Any]  # list[Root] when available
    project_name: str
    agent_info: Optional["AgentInfo"]
    client_params: Optional[dict[str, Any]]
    timestamp: float


# ContextVar for comprehensive MCP context cache (thread-safe)
cached_mcp_context: ContextVar[Optional[CachedMcpContext]] = ContextVar("cached_mcp_context", default=None)


async def cache_mcp_globals(ctx: Optional["Context"] = None) -> bool:  # type: ignore[type-arg]
    """Cache MCP globals (roots, agent info, client params) if context available.

    Args:
        ctx: Optional MCP Context (FastMCP auto-injects in tools)

    Returns:
        True if context was available and cached, False otherwise
    """
    if ctx is None:
        return False

    from time import time

    from mcp_guide.agent_detection import detect_agent

    # Initialize variables for comprehensive context
    roots = []
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
            # Continue - we can still cache agent info

        # Cache MCP context (even if roots failed)
        cached_mcp_context.set(
            CachedMcpContext(
                roots=roots,
                project_name="",  # Will be set by resolve_project_name
                agent_info=agent_info,
                client_params=client_params,
                timestamp=time(),
            )
        )
        return True

    except AttributeError:
        # Client doesn't support basic context - try to cache just agent info
        try:
            if hasattr(ctx, "session") and hasattr(ctx.session, "client_params") and ctx.session.client_params:
                client_params = ctx.session.client_params
                agent_info = detect_agent(client_params)
                cached_mcp_context.set(
                    CachedMcpContext(
                        roots=[],
                        project_name="",
                        agent_info=agent_info,
                        client_params=client_params,
                        timestamp=time(),
                    )
                )
                return True
        except Exception:
            # Cache write failed, continue without caching
            pass
        return False
    except Exception as e:
        logger.debug(f"Failed to cache MCP globals: {e}")
        return False


async def resolve_project_name() -> str:
    """Resolve project name from cached context or environment fallbacks.

    Resolution priority:
    1. Client roots (via cached MCP Context) - PRIMARY
    2. PWD environment variable - FALLBACK

    Returns:
        Project name string

    Raises:
        ValueError: If no project context is available
    """
    import os

    # Priority 1: Client roots from cached context
    cached = cached_mcp_context.get()
    if cached and cached.roots:
        first_root = cached.roots[0]
        if str(first_root.uri).startswith("file://"):
            parsed = urlparse(str(first_root.uri))
            project_path = Path(parsed.path)
            project_name = project_path.name
            if project_name:
                # Update cached context with resolved project name
                cached_mcp_context.set(
                    CachedMcpContext(
                        roots=cached.roots,
                        project_name=project_name,
                        agent_info=cached.agent_info,
                        client_params=cached.client_params,
                        timestamp=cached.timestamp,
                    )
                )
                return project_name

    # Priority 2: PWD environment variable
    pwd = os.environ.get("PWD")
    if pwd and Path(pwd).is_absolute():
        return Path(pwd).name

    raise ValueError("Project context not available. Call set_project() with the basename of your current directory.")


async def resolve_project_path() -> str:
    """Resolve full project path for hash calculation.

    Returns:
        Full absolute project path

    Raises:
        ValueError: If no project context is available
    """
    import os

    # Priority 1: Client roots from cached context
    cached = cached_mcp_context.get()
    if cached and cached.roots:
        first_root = cached.roots[0]
        if str(first_root.uri).startswith("file://"):
            parsed = urlparse(str(first_root.uri))
            return str(Path(parsed.path).resolve())

    # Priority 2: PWD environment variable
    pwd = os.environ.get("PWD")
    if pwd and Path(pwd).is_absolute():
        return str(Path(pwd).resolve())

    raise ValueError("Project context not available. Cannot determine project path.")
