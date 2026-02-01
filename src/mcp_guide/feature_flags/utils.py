"""Utility functions for flag resolution."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp_guide.session import Session


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
        return resolved_flags.get(flag_name, default)
    except Exception:
        # Return default if flag resolution fails
        return default
