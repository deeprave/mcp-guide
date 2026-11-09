"""Utility functions for flag resolution."""

from typing import TYPE_CHECKING, Any

from mcp_guide.core.mcp_log import get_logger

if TYPE_CHECKING:
    from mcp_guide.session import Session

logger = get_logger(__name__)


async def get_resolved_flag_value(session: "Session", flag_name: str, default: Any = None) -> Any:
    """Get resolved flag value with error handling.

    Args:
        session: The session to resolve flags from
        flag_name: Name of the flag to resolve
        default: Default value if flag not found

    Returns:
        The resolved flag value or default
    """
    try:
        from mcp_guide.models import resolve_all_flags

        resolved_flags = await resolve_all_flags(session)
        value = resolved_flags.get(flag_name, default)
        logger.trace(f"Flag resolution: {flag_name}={value!r}")
        return value
    except Exception as e:
        logger.trace(f"Flag resolution failed: {flag_name}, exception={e!r}, returning default={default!r}")
        return default


async def resolve_documents_path(session: "Session") -> str:
    """Resolve the validated documents path shared by rendering and startup tasks."""
    from mcp_guide.feature_flags.constants import DEFAULT_DOCUMENTS_PATH, FLAG_PATH_DOCUMENTS
    from mcp_guide.feature_flags.types import to_raw_feature_value
    from mcp_guide.feature_flags.validators import validate_path_flag

    value = await get_resolved_flag_value(session, FLAG_PATH_DOCUMENTS)
    if value is None:
        return DEFAULT_DOCUMENTS_PATH
    raw = to_raw_feature_value(value)
    path = raw if isinstance(raw, str) and validate_path_flag(raw, True) else DEFAULT_DOCUMENTS_PATH
    return f"{path.rstrip('/')}/"


async def resolve_runtime_default_read_paths(session: "Session") -> list[str]:
    """Return session-derived read roots without persisting them on Project."""
    from mcp_guide.feature_flags.constants import DEFAULT_DOCUMENTS_PATH
    from mcp_guide.models.constants import DEFAULT_ALLOWED_WRITE_PATHS

    root = session.bound_root_path
    worktree = session.worktree_path
    if root is None or worktree is None:
        return []

    documents_path = await resolve_documents_path(session)
    root_defaults = {
        str(root / documents_path),
        *(str(root / path) for path in DEFAULT_ALLOWED_WRITE_PATHS if path != DEFAULT_DOCUMENTS_PATH),
    }
    return [str(worktree), *sorted(root_defaults)]


async def resolve_effective_write_paths(session: "Session") -> list[str]:
    """Combine runtime defaults with persisted user-added write paths."""
    from mcp_guide.feature_flags.constants import DEFAULT_DOCUMENTS_PATH
    from mcp_guide.models.constants import DEFAULT_ALLOWED_WRITE_PATHS

    project = await session.get_project()
    documents_path = await resolve_documents_path(session)
    defaults = [documents_path if path == DEFAULT_DOCUMENTS_PATH else path for path in DEFAULT_ALLOWED_WRITE_PATHS]
    return [*defaults, *project.allowed_write_paths]
