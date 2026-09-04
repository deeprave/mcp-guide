"""Document management tools."""

from typing import Any

from pydantic import Field

from mcp_guide.core.arguments import Arguments as ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_NOT_FOUND
from mcp_guide.runtime import RequestContext
from mcp_guide.store.document_store import remove_document
from mcp_guide.tools.tool_result import ToolResult, tool_result


class DocumentRemoveArgs(ToolArguments):
    """Arguments for document_remove tool."""

    category: str = Field(description="Category the document belongs to")
    name: str = Field(description="Document name to remove")


async def internal_document_remove(
    args: DocumentRemoveArgs,
    request_context: RequestContext,
) -> Result[dict[str, Any]]:
    """Remove a document from the store."""
    removed = await remove_document(args.category, args.name)
    if not removed:
        return Result.failure(
            error=f"Document {args.category}/{args.name} not found",
            error_type=ERROR_NOT_FOUND,
        )
    return Result.ok(
        value={"category": args.category, "name": args.name},
        message=f"Document {args.category}/{args.name} removed",
    )


@toolfunc(DocumentRemoveArgs)
async def document_remove(args: DocumentRemoveArgs, request_context: RequestContext) -> ToolResult:
    """Remove a document from the store by category and name."""
    result = await internal_document_remove(args, request_context)
    return await tool_result("document_remove", result, session=request_context.session, session_id=args.session_id)
