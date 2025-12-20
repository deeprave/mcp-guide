"""MCP resource handlers for guide:// URI scheme."""

import logging
from typing import Any, Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_guide.server import resources
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content

logger = logging.getLogger(__name__)


@resources.resource("guide://{collection}/{document}")
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
        content_args = ContentArgs(category_or_collection=collection, pattern=document if document else None)

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
