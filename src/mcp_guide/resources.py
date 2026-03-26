"""MCP resource handlers for guide:// URI scheme."""

from typing import Optional

from fastmcp import Context

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.resource_decorator import resourcefunc
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource

logger = get_logger(__name__)


def _get_request_uri(ctx: Optional[Context]) -> str | None:
    """Return the current MCP request URI when FastMCP exposes it."""
    if ctx is None or ctx.request_context is None:
        return None
    request = ctx.request_context.request
    if request is None:
        return None
    params = getattr(request, "params", None)
    uri = getattr(params, "uri", None)
    if isinstance(uri, str) and uri.startswith("guide://"):
        return uri
    return None


async def _resolve_guide_uri(uri: str, ctx: Optional[Context]) -> str:
    """Resolve a guide:// URI through the shared read_resource implementation."""
    result = await internal_read_resource(ReadResourceArgs(uri=uri), ctx=ctx)
    if not result.success:
        return result.error or "Resource retrieval failed"
    return str(result.value) if result.value is not None else ""


@resourcefunc("guide://{collection}/{document}")
async def guide_resource(collection: str, document: str = "", ctx: Optional[Context] = None) -> str:
    """Read content from guide:// URI.

    Args:
        collection: Collection/category name
        document: Optional document pattern
        ctx: MCP context

    Returns:
        Content text
    """
    try:
        if collection.startswith("_"):
            uri = _get_request_uri(ctx) or f"guide://{collection}"
            if document:
                uri = f"{uri}/{document}"
            return await _resolve_guide_uri(uri, ctx)

        # Create ContentArgs for internal_get_content
        content_args = ContentArgs(expression=collection, pattern=document if document else None, force=False)

        # Delegate to internal content retrieval
        result = await internal_get_content(content_args, ctx)

        if not result.success:
            return result.error or "Content retrieval failed"

        return str(result.value) if result.value is not None else ""

    except (ValueError, FileNotFoundError, PermissionError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        # Log unexpected exceptions for debugging while still handling them
        logger.error(f"Unexpected error in guide_resource: {type(e).__name__}: {str(e)}", exc_info=True)
        return f"Unexpected error: {str(e)}"


@resourcefunc("guide://_{command_path*}")
async def guide_command_resource(command_path: str, ctx: Optional[Context] = None) -> str:
    """Read command output from guide:// command URIs.

    This template is advertised separately so MCP clients can discover command-shaped
    guide:// URIs via resource listing rather than only through the read_resource tool.
    """
    try:
        uri = _get_request_uri(ctx) or f"guide://_{command_path}"
        return await _resolve_guide_uri(uri, ctx)
    except (ValueError, FileNotFoundError, PermissionError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in guide_command_resource: {type(e).__name__}: {str(e)}", exc_info=True)
        return f"Unexpected error: {str(e)}"
