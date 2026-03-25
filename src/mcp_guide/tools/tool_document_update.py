"""Document update tool."""

from typing import Any, Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # ty: ignore[invalid-assignment]

from pydantic import Field

from mcp_guide.core.arguments import Arguments as ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_NOT_FOUND
from mcp_guide.store.document_store import update_document
from mcp_guide.tools.tool_result import tool_result


class DocumentUpdateArgs(ToolArguments):
    """Arguments for document_update tool."""

    category: str = Field(description="Category the document belongs to")
    name: str = Field(description="Document name to update")
    new_name: Optional[str] = Field(default=None, description="New document name")
    new_category: Optional[str] = Field(default=None, description="New category to move document to")
    metadata_add: Optional[dict[str, Any]] = Field(
        default=None, description="Metadata entries to merge into existing metadata"
    )
    metadata_replace: Optional[dict[str, Any]] = Field(
        default=None, description="Replace entire metadata with this dict"
    )
    metadata_clear: Optional[list[str]] = Field(default=None, description="List of metadata keys to remove")


async def internal_document_update(
    args: DocumentUpdateArgs,
    ctx: Optional[Context] = None,
) -> Result[dict[str, Any]]:
    """Update a document in the store."""
    # Validate target category exists if moving
    if args.new_category is not None:
        from mcp_guide.session import get_session

        session = await get_session()
        project = await session.get_project()
        if args.new_category not in project.categories:
            return Result.failure(error=f"Category {args.new_category!r} does not exist")

    try:
        record = await update_document(
            args.category,
            args.name,
            new_name=args.new_name,
            new_category=args.new_category,
            metadata_add=args.metadata_add,
            metadata_replace=args.metadata_replace,
            metadata_clear=args.metadata_clear,
        )
    except ValueError as e:
        return Result.failure(error=str(e))

    if record is None:
        return Result.failure(
            error=f"Document {args.category}/{args.name} not found",
            error_type=ERROR_NOT_FOUND,
        )

    return Result.ok(
        value={"category": record.category, "name": record.name, "metadata": record.metadata},
        message=f"Document {args.category}/{args.name} updated",
    )


@toolfunc(DocumentUpdateArgs)
async def document_update(args: DocumentUpdateArgs, ctx: Optional[Context] = None) -> str:
    """Update a stored document: rename, move between categories, or modify metadata."""
    result = await internal_document_update(args, ctx)
    return await tool_result("document_update", result)
