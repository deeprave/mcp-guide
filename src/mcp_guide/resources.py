"""MCP resource handlers for guide:// URI scheme."""

from typing import Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.resource_decorator import resourcefunc

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_guide.tools.tool_content import ContentArgs, internal_get_content

logger = get_logger(__name__)


@resourcefunc("guide://{collection}/{document}")
async def guide_resource(collection: str, document: str = "", ctx: Optional["Context[Any, Any, Any]"] = None) -> str:
    """Read content from guide:// URI.

    Args:
        collection: Collection/category name
        document: Optional document pattern
        ctx: MCP context

    Returns:
        Content text
    """
    try:
        # Create ContentArgs for internal_get_content
        content_args = ContentArgs(expression=collection, pattern=document if document else None)

        # Delegate to internal content retrieval
        result = await internal_get_content(content_args, ctx)

        if not result.success:
            return result.error or "Content retrieval failed"

        return str(result.value) if result.value else ""

    except (ValueError, FileNotFoundError, PermissionError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        # Log unexpected exceptions for debugging while still handling them
        logger.error(f"Unexpected error in guide_resource: {type(e).__name__}: {str(e)}", exc_info=True)
        return f"Unexpected error: {str(e)}"
