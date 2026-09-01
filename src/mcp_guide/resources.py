"""MCP resource handlers for guide:// URI scheme."""

from typing import Any, Optional

from fastmcp import Context

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.resource_decorator import resourcefunc
from mcp_guide.mcp_context import resource_uri_from_fastmcp
from mcp_guide.mcp_result_adapter import resource_response
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_INVALID_NAME, make_invalid_session_result
from mcp_guide.session import InvalidGuideSessionError, Session, get_session
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource
from mcp_guide.validation import InvalidProjectNameError

logger = get_logger(__name__)


async def _resolve_resource_session(
    ctx: Optional[Context], session_id: str | None
) -> tuple[Session | None, str | None]:
    """Resolve the request Session once for a native resource read."""
    try:
        session = await get_session(ctx, session_id=session_id)
    except InvalidGuideSessionError:
        raise
    except InvalidProjectNameError:
        raise
    except RuntimeError as error:
        logger.debug("Skipping session resolution for resource call without an active Session: %s", error)
        return None, session_id
    return session, session.session_id


async def _process_and_serialize(result: Result[Any], session: Session | None) -> object:
    """Run a Result through the already-resolved Session and adapt it once."""
    resolved_session_id = session.session_id if session is not None else None
    try:
        if session is not None:
            result = await session.task_manager.process_result(result)
    except Exception as e:
        logger.error(f"TaskManager processing failed for resource: {e}")
    return resource_response(result, session_id=resolved_session_id)


async def _resolve_guide_uri(
    uri: str, ctx: Optional[Context], session: Session | None, resolved_id: str | None
) -> object:
    """Resolve a guide:// URI through the shared read_resource implementation."""
    result = await internal_read_resource(ReadResourceArgs(uri=uri, session_id=resolved_id), ctx=ctx, session=session)
    return await _process_and_serialize(result, session)


@resourcefunc("guide://{collection}/{document}{?session_id}")
async def guide_resource(
    collection: str, document: str = "", ctx: Optional[Context] = None, session_id: str | None = None
) -> object:
    """Read content from guide:// URI.

    Args:
        collection: Collection/category name
        document: Optional document pattern
        ctx: MCP context

    Returns:
        Native MCP response preserving the Guide result payload
    """
    try:
        session, resolved_id = await _resolve_resource_session(ctx, session_id)
        if collection.startswith("_"):
            uri = resource_uri_from_fastmcp(ctx) or f"guide://{collection}"
            if document:
                uri = f"{uri}/{document}"
            return await _resolve_guide_uri(uri, ctx, session, resolved_id)

        # For guide://policies/<topic>, append a trailing slash to the document so that
        # gather_category_fileinfos treats it as a sub-path filter against the project's
        # configured patterns rather than a direct pattern override.
        pattern: str | None
        if collection == "policies" and document:
            pattern = document + "/"
        else:
            pattern = document if document else None

        content_args = ContentArgs(expression=collection, pattern=pattern, force=False, session_id=resolved_id)
        result = await internal_get_content(content_args, ctx, session=session)
        return await _process_and_serialize(result, session)

    except InvalidGuideSessionError:
        return resource_response(make_invalid_session_result())
    except InvalidProjectNameError as error:
        return resource_response(Result.failure(str(error), error_type=ERROR_INVALID_NAME))
    except (ValueError, FileNotFoundError, PermissionError) as e:
        return resource_response(Result.failure(str(e)))
    except Exception as e:
        # Log unexpected exceptions for debugging while still handling them
        logger.error(f"Unexpected error in guide_resource: {type(e).__name__}: {str(e)}", exc_info=True)
        return resource_response(Result.failure(f"Unexpected error: {str(e)}"))


@resourcefunc("guide://_{command_path*}{?session_id}")
async def guide_command_resource(
    command_path: str, ctx: Optional[Context] = None, session_id: str | None = None
) -> object:
    """Read command output from guide:// command URIs.

    This template is advertised separately so MCP clients can discover command-shaped
    guide:// URIs via resource listing rather than only through the read_resource tool.
    """
    try:
        session, resolved_id = await _resolve_resource_session(ctx, session_id)
        uri = resource_uri_from_fastmcp(ctx) or f"guide://_{command_path}"
        return await _resolve_guide_uri(uri, ctx, session, resolved_id)
    except InvalidGuideSessionError:
        return resource_response(make_invalid_session_result())
    except InvalidProjectNameError as error:
        return resource_response(Result.failure(str(error), error_type=ERROR_INVALID_NAME))
    except (ValueError, FileNotFoundError, PermissionError) as e:
        return resource_response(Result.failure(str(e)))
    except Exception as e:
        logger.error(f"Unexpected error in guide_command_resource: {type(e).__name__}: {str(e)}", exc_info=True)
        return resource_response(Result.failure(f"Unexpected error: {str(e)}"))
