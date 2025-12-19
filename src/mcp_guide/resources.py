"""MCP resource handlers for guide:// URI scheme."""

from typing import Any, Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_guide.tools.tool_content import ContentArgs, internal_get_content


def register_resource_handlers(mcp_server: Any) -> None:
    """Register resource handlers with MCP server."""

    @mcp_server.resource("guide://{collection}/{document}")  # type: ignore[untyped-decorator]
    async def guide_resource(collection: str, document: str = "", ctx: Optional["Context"] = None) -> str:  # type: ignore[type-arg]
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

        except Exception as e:
            return f"Unexpected error: {str(e)}"
