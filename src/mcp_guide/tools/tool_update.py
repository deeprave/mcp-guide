# See src/mcp_guide/tools/README.md for tool documentation standards

"""Documentation update tool."""

from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.installer.core import ORIGINAL_ARCHIVE, perform_locked_update, read_version
from mcp_guide.lazy_path import LazyPath
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_CONFIG_READ, ERROR_FILE_ERROR
from mcp_guide.runtime import RequestContext, get_runtime
from mcp_guide.tools.tool_result import ToolResult, tool_result

__all__ = ["internal_update_documents", "update_documents"]


class UpdateDocumentsArgs(ToolArguments):
    """Arguments for update_documents tool."""

    pass


async def internal_update_documents(
    args: UpdateDocumentsArgs,
    request_context: RequestContext,
) -> Result[dict]:
    """Update documentation files using the configured docroot.

    Checks for version changes and updates files using smart merge strategy.
    Uses file locking to prevent concurrent updates.

    Args:
        args: Tool arguments (currently no parameters)
        request_context: Resolved application request context

    Returns:
        Result containing update statistics
    """
    try:
        session = request_context.session
        docroot = LazyPath(await get_runtime().get_docroot()).resolve()
        archive_path = docroot / ORIGINAL_ARCHIVE
    except (OSError, ValueError, RuntimeError) as e:
        return Result.failure(f"Failed to resolve documentation root: {e}", error_type=ERROR_CONFIG_READ)

    # Check version
    from mcp_guide import __version__

    try:
        current_version = await read_version(docroot)
    except OSError as e:
        return Result.failure(f"Failed to read installed documentation version: {e}", error_type=ERROR_FILE_ERROR)
    if current_version == __version__:
        return Result.ok(value={"message": f"Already at version {__version__}", "updated": False})

    # Perform locked update
    try:
        stats = await perform_locked_update(docroot, archive_path)
    except OSError as e:
        return Result.failure(f"Failed to update documentation: {e}", error_type=ERROR_FILE_ERROR)

    # Acknowledge update prompt to stop retry loop
    from mcp_guide.tasks.update_task import McpUpdateTask

    update_task = session.task_manager.get_task_by_type(McpUpdateTask)
    if update_task:
        await update_task.acknowledge_update()

    return Result.ok(
        value={
            "message": "Documentation updated successfully",
            "updated": True,
            "stats": stats,
        }
    )


@toolfunc(UpdateDocumentsArgs, requires_project=False)
async def update_documents(
    args: UpdateDocumentsArgs,
    request_context: RequestContext,
) -> ToolResult:
    """Update documentation files using the configured docroot.

    Checks for version changes and updates files using smart merge strategy.
    Uses file locking to prevent concurrent updates.
    """
    result = await internal_update_documents(args, request_context)
    return await tool_result("update_documents", result, session=request_context.session, session_id=args.session_id)
